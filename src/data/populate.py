from pathlib import Path

from pandas import read_csv, to_datetime

from src.data.utils import csv_filename, iso_to_date_str
from src.db.repo import (
    CountsRepo,
    DateSamplingRunRepo,
    StationRepo,
    StationSamplingRunRepo,
)
from src.db.session import SessionLocal
from src.utils.day_types import get_day_type


def window_min_str(window_int):
    return f"{window_int}min"


def build_counts(counts_df, station_id, window_int):

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
                "count_in": row["count_in"],
                "window_minutes": window_int,
            }
        )

        return counts


def compute_counts(station_df, station_id, window_int, time_min: int, time_max: int):
    if station_df.empty:
        return []

    station_df["time"] = to_datetime(station_df["time"])
    station_df = station_df.sort_values("time")
    station_df["window"] = station_df["time"].dt.floor(window_min_str(window_int))
    counts_df = station_df.groupby("window").size().reset_index(name="count_in")

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
    counts = build_counts(counts_df, station_id, window_int)

    return counts


def populate_check_ins(
    dsrun_id: int,
    ssrun_id: int,
    path: Path,
    window_int,
    time_min,
    time_max,
):
    db = SessionLocal()

    # init repos
    station_repo = StationRepo(db)
    ssrun_repo = StationSamplingRunRepo(db)
    dsrun_repo = DateSamplingRunRepo(db)
    counts_repo = CountsRepo(db)

    # fetch station sampling results, and store the stations
    ssrun = ssrun_repo.get_by(id=ssrun_id)
    station_repo.bulk_insert(ssrun.sampled_stations)
    station_codes = [s["code"] for s in ssrun.sampled_stations]

    dsrun = dsrun_repo.get_by(id=dsrun_id)
    for dt_str in dsrun.sampled_dates:
        date_str = iso_to_date_str(dt_str)
        df = read_csv(csv_filename(path, date_str))
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
            )

            all_counts.extend(station_counts)

        counts_repo.bulk_upsert_in(all_counts)

    # counts for check-outs logic
    # skip if file processed: check sample dates, use files repo
    # mark file processed
