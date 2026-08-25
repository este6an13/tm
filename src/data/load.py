from datetime import date

from pandas import DataFrame

from src.db.repo import CountsRepo
from src.db.session import SessionLocal


# this construction ensures colums will be sorted (asc)
def time_columns(time_min: int = 400, time_max: int = 2300, window_minutes: int = 15):
    col_time = time_min
    cols = []
    while col_time <= time_max:
        cols.append("ti_" + str(col_time))  # check-ins
        cols.append("to_" + str(col_time))  # check-outs
        col_hour = col_time // 100
        col_minutes = col_time % 100
        col_minutes += window_minutes
        col_hour += 1 if col_minutes >= 60 else 0
        col_minutes = 0 if col_minutes >= 60 else col_minutes
        col_time = col_hour * 100 + col_minutes
    return cols


def counts_dataframe(counts):
    return DataFrame(
        [
            {
                "year": c.year,
                "month": c.month,
                "day": c.day,
                "time": c.time,
                "day_type": c.day_type,
                "count_in": c.count_in,
                "count_out": c.count_out,
                "station_id": c.station_id,
                "station_code": c.station.code,
                "station_name": c.station.name,
            }
            for c in counts
        ]
    ).fillna(0)


# transform counts_df an "expanded" df in which each row is uniquely
# identified by a key, and each row is expanded with time (ti_, to_) columns.
# we want one record per (date, station_id)
def t_counts_dataframe(counts_df, time_cols):
    t_counts = []
    for c in counts_df.itertuples(index=True):
        key = (c.year, c.month, c.day, c.station_id)
        # if record deosn't exist, create it with a key to identify it
        if not any(tc["key"] == key for tc in t_counts):
            t_counts.append(
                {
                    "key": key,  # used for identifying and searching
                    "year": c.year,
                    "month": c.month,
                    "day": c.day,
                    "time": c.time,
                    "day_type": c.day_type,
                    "station_id": c.station_id,
                    "station_code": c.station_code,
                    "station_name": c.station_name,
                }
            )
        # find existing record using the key
        tc = next(_tc for _tc in t_counts if _tc["key"] == key)
        ti_col = "ti_" + str(c.time)
        to_col = "to_" + str(c.time)
        # not checking, assuming col must be present
        tc[ti_col] = c.count_in
        tc[to_col] = c.count_out

    t_counts_df = DataFrame(
        t_counts,
        columns=[
            "year",
            "month",
            "day",
            "time",
            "day_type",
            "station_id",
            "station_code",
            "station_name",
        ]
        + time_cols,
    )

    return t_counts_df


def load_counts(
    time_min: int = 400,
    time_max: int = 2300,
    station_ids=None,
    dates: list[date] | None = None,
    **filters,
):
    db = SessionLocal()

    counts_repo = CountsRepo(db)
    counts = counts_repo.get_by(
        station_ids=station_ids,
        dates=dates,
        time_min=time_min,
        time_max=time_max,
        **filters,
    )
    counts_df = counts_dataframe(counts)
    t_counts_df = t_counts_dataframe(
        counts_df,
        time_columns(
            time_min=time_min,
            time_max=time_max,
            window_minutes=filters.get("window_minutes"),
        ),
    )
    return t_counts_df
