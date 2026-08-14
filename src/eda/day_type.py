from pandas import DataFrame, concat
from scipy.spatial.distance import pdist, squareform

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
            distances = pdist(ti_series_matrix, metric="euclidean")
            print(station_code, day_type)
            print(ti_series_matrix)
            print(ti_series_matrix.shape)
            print(distances.shape)
            print(squareform(distances))
            # we can report mean and std on these matrices
            # I can plot the matrices for visbility
            # this is within day type group analysis

        # between groups separation
        # I sample N rows per day type, to form N matrices
        # each matrix has 1 row per distance type
        # I'll perform the distance mean/std analysis on each
        # at the end I'll average
        # N should be adaptative based on size
        # seed needs to be defined in constants
        matrices = []
        N = 1
        samples = {}
        for day_type, day_type_df in ti_series_groups:
            samples[day_type] = day_type_df.drop(columns=["day_type"]).sample(
                n=N, random_state=42
            )
        for i in range(N):
            matrix = concat(
                [samples[dt].iloc[i] for dt in ["HO", "SU", "SA", "WD"]]
            ).values
            matrices.append(matrix)
            print(matrix)

        # decompose everything in smaller functions


separation()
