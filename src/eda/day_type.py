from itertools import combinations

from numpy import concatenate, median, percentile, quantile, triu
from numpy.random import choice
from scipy.spatial.distance import cdist, pdist, squareform

from src.data.load import load_counts
from src.eda.utils import artifacts
from src.utils.day_types import DAY_TYPES

BOOTSTRAP_ITER = 5000  # this will be considered a config value

DAY_TYPE_PAIRS = list(combinations(DAY_TYPES, 2))


def station_time_series(station_df):
    ti_cols = sorted([col for col in station_df.columns if col.startswith("ti_")])
    to_cols = sorted([col for col in station_df.columns if col.startswith("to_")])
    ti_series = station_df[["day_type"] + ti_cols]
    to_series = station_df[["day_type"] + to_cols]
    ti_series = ti_series.fillna(0)
    to_series = to_series.fillna(0)
    return ti_series, to_series


# sample N rows with replacement
def sample_with_replacement(arr):
    N = len(arr)
    idx = choice(range(N), N)
    return arr[idx]


def station_day_type_matrices(t_series_df, bootstrap=False):
    sg_matrices = {}
    t_series_groups = t_series_df.groupby("day_type")
    for day_type, day_type_df in t_series_groups:
        ti_series_matrix = day_type_df.drop(columns=["day_type"]).values
        sg_matrices[day_type] = (
            sample_with_replacement(ti_series_matrix) if bootstrap else ti_series_matrix
        )
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


def _analyze_time_series(t_series_df, bootstrap=False):
    sg_matrices = station_day_type_matrices(t_series_df, bootstrap)
    w_means = within_groups_analysis(sg_matrices)
    b_mean = between_groups_analysis(sg_matrices)
    res = []
    for day_type, w_mean in w_means.items():
        R = b_mean / w_mean
        res.append((day_type, R))
    return res


def repeat_time_series_analysis(t_series_df):
    results = {}
    intervals = {}
    for _ in range(BOOTSTRAP_ITER):
        # perform 1 bootstrap iteration
        partial_result = _analyze_time_series(t_series_df, bootstrap=True)
        # aggregate results
        for day_type, R in partial_result:
            results.setdefault(day_type, []).append(R)

    # compute CI per day_type
    for day_type, arr in results.items():
        q025, q975 = quantile(arr, [0.025, 0.975])
        intervals[day_type] = (q025, q975)

    return intervals


def analyze_time_series(t_series_df, bootstrap=False):
    obs = _analyze_time_series(t_series_df)
    if bootstrap:
        intervals = repeat_time_series_analysis(t_series_df)

    # organize results
    results = {}
    for day_type, R in obs:
        results[day_type] = (R, intervals[day_type])
    return results


def analyze_station(station_df, bootstrap=False):
    ti_series_df, to_series_df = station_time_series(station_df)
    ins_results = analyze_time_series(ti_series_df, bootstrap)  # check-ins
    outs_results = analyze_time_series(to_series_df, bootstrap)  # check-outs

    return ins_results, outs_results


def analysis():

    TIME_MIN = 400
    TIME_MAX = 2300
    WINDOW_MINUTES = 15

    counts_df = load_counts(
        time_min=TIME_MIN,
        time_max=TIME_MAX,
        station_ids=[1, 2, 6, 8, 9, 10, 11, 14, 18, 20, 21, 22, 25, 29],
        window_minutes=WINDOW_MINUTES,
    )
    station_groups = counts_df.groupby("station_id")

    ins_agg_results = {}
    outs_agg_results = {}

    _sg_r_ci_table_ins = []
    _sg_r_ci_table_outs = []

    for station_id, station_df in station_groups:
        station_code = station_df.iloc[0]["station_code"]
        station_name = station_df.iloc[0]["station_name"]
        ins_results, outs_results = analyze_station(station_df, bootstrap=True)

        # results are of the form {'WD': (observed R, (lo, hi)), ...}
        # (lo, hi) is the confidence interval constructed with bootstrap
        # observed R is the actual R per day type (between/within) computed from the
        # time series dataset without bootstrap sampling (that is the original dataset)
        for day_type in ins_results:
            ins_agg_results.setdefault(day_type, []).append(ins_results[day_type])
            outs_agg_results.setdefault(day_type, []).append(outs_results[day_type])

            # building sg_r_ci_table_ins artifact input
            _sg_r_ci_table_ins.append(
                (
                    station_id,
                    station_code,
                    station_name,
                    day_type,
                    ins_results[day_type][0],  # observed R
                    ins_results[day_type][1][0],  # CI low
                    ins_results[day_type][1][1],  # CI high
                )
            )

            artifacts.sg_r_ci_table_ins(_sg_r_ci_table_ins)  # persistance

            # building sg_r_ci_table_outs artifact input
            _sg_r_ci_table_outs.append(
                (
                    station_id,
                    station_code,
                    station_name,
                    day_type,
                    outs_results[day_type][0],  # observed R
                    outs_results[day_type][1][0],  # CI low
                    outs_results[day_type][1][1],  # CI high
                )
            )

            artifacts.sg_r_ci_table_outs(_sg_r_ci_table_outs)  # persistance

    # these results are a table, each row a day type
    # the median R is the median observed R across stations
    # p is the proportion of stations with lower CI value > 1

    # For check-ins
    for day_type, results in ins_agg_results.items():
        median_R = median([R for R, _ in results])
        q25, q75 = percentile([R for R, _ in results], [25, 75])
        p = sum([1 if CI[0] > 1 else 0 for _, CI in results]) / len(station_groups)

        print(day_type, median_R, q25, q75, p)

    # for check-outs
    for day_type, results in outs_agg_results.items():
        median_R = median([R for R, _ in results])
        q25, q75 = percentile([R for R, _ in results], [25, 75])
        p = sum([1 if CI[0] > 1 else 0 for _, CI in results]) / len(station_groups)

        print(day_type, median_R, q25, q75, p)


if __name__ == "__main__":
    analysis()
