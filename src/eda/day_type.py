from itertools import combinations

from numpy import concatenate
from pandas import DataFrame
from scipy.spatial.distance import cdist, pdist, squareform

from src.db.repo import CountsRepo
from src.db.session import SessionLocal


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


def station_time_series(station_df):
    ti_cols = sorted([col for col in station_df.columns if col.startswith("ti_")])
    to_cols = sorted([col for col in station_df.columns if col.startswith("to_")])
    ti_series = station_df[["day_type"] + ti_cols]
    to_series = station_df[["day_type"] + to_cols]
    ti_series = ti_series.fillna(0)
    return ti_series, to_series


def separation():

    time_cols = time_columns()
    day_type_pairs = list(combinations(["WD", "SA", "SU", "HO"], 2))

    db = SessionLocal()

    counts_repo = CountsRepo(db)
    counts = counts_repo.get_all()
    counts_df = counts_dataframe(counts)
    t_counts_df = t_counts_dataframe(counts_df, time_cols)
    station_groups = t_counts_df.groupby("station_code")
    time_cols = time_columns()
    for station_code, station_df in station_groups:
        ti_series_df, _ = station_time_series(station_df)
        ti_series_groups = ti_series_df.groupby("day_type")
        # within group analysis
        day_type_series = {}  # store them for between group analysis
        Dwg_means = []
        for day_type, day_type_df in ti_series_groups:
            # per (station, day_type) we have a number of time series
            # a time series is a 1D vector of n components
            # pdist calculate the distances between every pair (itself ignore since it's 0)
            # I use euclidean distance (sqrt of pair-wise components difference squared, a scalar)
            # this gives a 1D vector of m-components
            # according to docs, the formula is: dist(u=X[i], v=X[j]) is stored in entry m * i + j - ((i + 2) * (i + 1)) // 2.
            # squareform turns this vector interpretable into a distance matrix
            # so for our use case we should alwsys use squareform(pdist(...))
            ti_series_matrix = day_type_df.drop(columns=["day_type"]).values
            Dwg = squareform(pdist(ti_series_matrix, metric="euclidean"))
            Dwg_means.append(Dwg.mean())
            day_type_series[day_type] = ti_series_matrix
            # extract upper triangle excluding diagonal

        distance_matrices = []
        for g1, g2 in day_type_pairs:
            Dbg = cdist(day_type_series[g1], day_type_series[g2], metric="euclidean")
            distance_matrices.append(Dbg.ravel())  # ravel to 1D

        Db = concatenate(distance_matrices)
        for Dwg_mean in Dwg_means:
            print(station_code, "R = ", Db.mean() / Dwg_mean)

        # decompose everything in smaller functions


separation()
