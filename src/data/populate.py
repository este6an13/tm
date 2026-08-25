from os.path import isfile
from pathlib import Path
from typing import Literal

from pandas import read_csv, to_datetime

from src.data.utils import csv_filename, iso_to_date_str
from src.db.repo import (
    CountsRepo,
    DateSamplingRunRepo,
    ProcessedFileRepo,
    StationRepo,
    StationSamplingRunRepo,
)
from src.db.session import SessionLocal
from src.utils.day_types import get_day_type
from src.utils.logging import error, success, warning


def window_min_str(window_int):
    return f"{window_int}min"


def build_counts(
    counts_df,
    station_id,
    window_int,
    col: str = Literal["count_in", "count_out"],
):

    counts = []
    for _, row in counts_df.iterrows():
        timestamp = row["window"]
        day_type = get_day_type(timestamp)
        counts.append(
            {
                "year": row["year"],
                "month": row["month"],
                "day": row["day"],
                "day_of_week": row["day_of_week"],
                "time": row["time_int"],
                "day_type": day_type,
                "station_id": station_id,
                col: row[col],
                "window_minutes": window_int,
            }
        )

    return counts


def compute_count_column(station_df, col):
    if col == "count_in":
        # each row is one event
        return station_df.groupby("window").size().reset_index(name=col)
    elif col == "count_out":
        # one row has multiple events, so we add them
        return station_df.groupby("window")["events"].sum().reset_index(name=col)
    else:
        raise ValueError("col must be either count_in or count_out")


def compute_counts(
    station_df,
    station_id,
    window_int: int = 15,
    time_min: int = 400,
    time_max: int = 2300,
    col: str = Literal["count_in", "count_out"],
):
    if station_df.empty:
        return []

    station_df["time"] = to_datetime(station_df["time"])
    station_df = station_df.sort_values("time")
    station_df["window"] = station_df["time"].dt.floor(window_min_str(window_int))
    counts_df = compute_count_column(station_df, col)

    # Add time breakdown columns
    counts_df["year"] = counts_df["window"].dt.year
    counts_df["month"] = counts_df["window"].dt.month
    counts_df["day"] = counts_df["window"].dt.day
    counts_df["day_of_week"] = counts_df["window"].dt.dayofweek
    counts_df["time_int"] = (
        counts_df["window"].dt.hour * 100 + counts_df["window"].dt.minute
    )

    counts_df = counts_df[
        (counts_df["time_int"] >= time_min) & (counts_df["time_int"] <= time_max)
    ]

    # Prepare dicts for bulk upsert
    counts = build_counts(counts_df, station_id, window_int, col)

    return counts


def movement_type_to_col(movement_type: Literal["INS", "OUTS"]):
    match movement_type:
        case "INS":
            return "count_in"
        case "OUTS":
            return "count_out"
        case _:
            raise ValueError("movement type must be either 'INS' or 'OUTS'")


def validate_window(window_int, movement_type):
    if window_int <= 0:
        raise ValueError("window_int must be positive")
    if not isinstance(window_int, int):
        raise TypeError("window_int must be an integer")
    if movement_type == "OUTS" and window_int % 15 != 0:
        raise ValueError("window_int must be a multiple of 15 for check-outs")


def process_type_str(movement_type, window_int):
    return f"{movement_type.lower()}-{window_int}-min"


def populate_counts(
    dsrun_id: int,
    ssrun_id: int,
    path: Path,
    movement_type: Literal["INS", "OUTS"],
    window_int: int = 15,
    time_min: int = 400,
    time_max: int = 2300,
    repopulate: bool = False,
):

    validate_window(window_int, movement_type)
    col = movement_type_to_col(movement_type)
    process_type = process_type_str(movement_type, window_int)

    db = SessionLocal()

    # init repos
    station_repo = StationRepo(db)
    ssrun_repo = StationSamplingRunRepo(db)
    dsrun_repo = DateSamplingRunRepo(db)
    counts_repo = CountsRepo(db)
    pfile_repo = ProcessedFileRepo(db)

    # fetch station sampling results, and store the stations
    ssrun = ssrun_repo.get_by(id=ssrun_id)
    station_repo.bulk_insert(ssrun.sampled_stations)
    station_codes = [s["code"] for s in ssrun.sampled_stations]

    dsrun = dsrun_repo.get_by(id=dsrun_id)
    for dt_str in dsrun.sampled_dates:
        date_str = iso_to_date_str(dt_str)

        is_processed = pfile_repo.is_processed(
            filename=date_str,
            process_type=process_type,
        )

        if not repopulate and is_processed:
            warning(
                f"⏩ file {date_str} for process {process_type} already populated, skipping"
            )
            continue

        csv_fname = csv_filename(path, date_str)
        if not isfile(csv_fname):
            error(f"❌ file {csv_fname} was not found")
            continue

        df = read_csv(csv_fname)

        if "station_code" not in df:
            error_msg = f"❌ file {csv_fname} was not post-processed: please remove it manually and re-start the pipeline"
            error(error_msg)
            raise RuntimeError(error_msg)

        df = df[df["station_code"].isin(station_codes)]
        station_groups = df.groupby("station_code")

        all_counts = []
        for station_code, station_df in station_groups:
            station = station_repo.get_by(code=station_code)
            if not station:
                continue

            station_counts = compute_counts(
                station_df,
                station.id,
                window_int,
                time_min,
                time_max,
                col=col,
            )

            all_counts.extend(station_counts)

        counts_repo.bulk_upsert(all_counts, col=col)

        pfile_repo.mark_processed(
            filename=date_str,
            process_type=process_type,
        )

        success(
            f"💾 file {date_str} for process {process_type} successfully populated!"
        )
