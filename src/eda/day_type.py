from itertools import combinations

from numpy import concatenate, triu
from scipy.spatial.distance import cdist, pdist, squareform

from src.data.load import load_counts
from src.utils.day_types import DAY_TYPES

DAY_TYPE_PAIRS = list(combinations(DAY_TYPES, 2))


def station_time_series(station_df):
    ti_cols = sorted([col for col in station_df.columns if col.startswith("ti_")])
    to_cols = sorted([col for col in station_df.columns if col.startswith("to_")])
    ti_series = station_df[["day_type"] + ti_cols]
    to_series = station_df[["day_type"] + to_cols]
    ti_series = ti_series.fillna(0)
    to_series = to_series.fillna(0)
    return ti_series, to_series


def station_day_type_matrices(t_series_df):
    sg_matrices = {}
    t_series_groups = t_series_df.groupby("day_type")
    for day_type, day_type_df in t_series_groups:
        ti_series_matrix = day_type_df.drop(columns=["day_type"]).values
        sg_matrices[day_type] = ti_series_matrix
    return sg_matrices


def within_groups_analysis(sg_matrices):
    means = {}
    for g in DAY_TYPES:
        dist_matrix = squareform(pdist(sg_matrices[g], metric="euclidean"))
        U = triu(dist_matrix)  # upper triangle
        mean = U[U != 0].mean()  # exclude diagonal
        means[g] = mean
    return means


def between_groups_analysis(sg_matrices):
    dist_arrays = []
    for g1, g2 in DAY_TYPE_PAIRS:
        pair_dist_matrix = cdist(sg_matrices[g1], sg_matrices[g2], metric="euclidean")
        pair_dist_array = pair_dist_matrix.ravel()  # 1D to concatenate
        dist_arrays.append(pair_dist_array)

    dist_matrix = concatenate(dist_arrays)
    return dist_matrix.mean()


def analyze_time_series(t_series_df):
    sg_matrices = station_day_type_matrices(t_series_df)
    w_means = within_groups_analysis(sg_matrices)
    b_mean = between_groups_analysis(sg_matrices)
    for day_type, w_mean in w_means.items():
        print(day_type, "R = ", b_mean / w_mean)


def analyze_station(station_df):
    ti_series_df, to_series_df = station_time_series(station_df)
    analyze_time_series(ti_series_df)  # check-ins
    analyze_time_series(to_series_df)  # check-outs


def separation():

    counts_df = load_counts(station_id=1)
    station_groups = counts_df.groupby("station_code")

    for _, station_df in station_groups:
        print(station_df["station_name"].head(1))
        analyze_station(station_df)


separation()
