from datetime import date
from itertools import combinations

from numpy import concatenate, quantile
from numpy.random import default_rng
from scipy.spatial.distance import cdist, pdist

from src.data.load import load_counts
from src.data.sampling.dates import sample_dates
from src.eda.utils import TIME_SERIES_PREFIX_COLS, station_time_series
from src.utils.seeds import SEED_BOOTSTRAP_SG_TIME_SERIES

BOOTSTRAP_ITER = 5000

rng = default_rng(SEED_BOOTSTRAP_SG_TIME_SERIES)

QUARTERS = range(1, 5)
QUARTERS_PAIRS = list(combinations(QUARTERS, 2))


# sample N rows with replacement
def sample_with_replacement(arr):
    N = len(arr)
    idx = rng.choice(range(N), N)
    return arr[idx]


def station_quarters_matrices(day_type_df, bootstrap=False):
    sq_matrices = {}
    # compute quarter column from month (m - 1) // 3 + 1
    day_type_df = day_type_df.assign(quarter=(day_type_df["month"] - 1) // 3 + 1)
    for quarter, quarter_df in day_type_df.groupby("quarter"):
        matrix = quarter_df.drop(columns=TIME_SERIES_PREFIX_COLS).values
        sq_matrices[quarter] = sample_with_replacement(matrix) if bootstrap else matrix
    return sq_matrices


def within_quarters_analysis(sq_matrices):
    dist_arrays = {}
    means = {}
    for q in QUARTERS:
        dist_array = pdist(sq_matrices[q], metric="euclidean")
        mean = dist_array.mean()  # already excludes diagonal
        means[q] = mean
        dist_arrays[q] = dist_array
    return means, dist_arrays


def between_quarters_analysis(sq_matrices):
    dist_arrays = {}
    for q1, q2 in QUARTERS_PAIRS:
        pair_dist_matrix = cdist(sq_matrices[q1], sq_matrices[q2], metric="euclidean")
        pair_dist_array = pair_dist_matrix.ravel()  # 1D to concatenate
        dist_arrays[(q1, q2)] = pair_dist_array

    dist_matrix = concatenate(list(dist_arrays.values()))
    return dist_matrix.mean(), dist_arrays


def _analyze_time_series(t_series_df, bootstrap=False):
    sq_matrices = station_quarters_matrices(t_series_df, bootstrap)
    w_means, w_dists = within_quarters_analysis(sq_matrices)
    b_mean, b_dists = between_quarters_analysis(sq_matrices)
    res = []
    for quarter, w_mean in w_means.items():
        R = b_mean / w_mean
        res.append((quarter, R))
    return res, w_dists, b_dists


def repeat_time_series_analysis(t_series_df):
    results = {}
    intervals = {}
    for _ in range(BOOTSTRAP_ITER):
        # perform 1 bootstrap iteration
        partial_result, _, _ = _analyze_time_series(t_series_df, bootstrap=True)
        # aggregate results
        for quarter, R in partial_result:
            results.setdefault(quarter, []).append(R)

    # compute CI per day_type
    for quarter, arr in results.items():
        q025, q975 = quantile(arr, [0.025, 0.975])
        intervals[quarter] = (q025, q975)

    return intervals


def analyze_time_series(t_series_df, bootstrap=False):
    for day_type, day_type_df in t_series_df.groupby("day_type"):
        obs, _, _ = _analyze_time_series(day_type_df)
        if bootstrap:
            intervals = repeat_time_series_analysis(day_type_df)

        # organize results
        results = {}
        for quarter, R in obs:
            key = (day_type, quarter)
            results[key] = (R, intervals[quarter])
            print(
                day_type,
                quarter,
                round(R, 5),
                f"({round(intervals[quarter][0], 5)}, {round(intervals[quarter][1], 5)})",
            )
        print()
    print()


def analyze_station(station_df, bootstrap=False):
    ti_series_df, to_series_df = station_time_series(station_df)
    # dists shapes are nested: [{q1: w1, ...} {p1: b1, ...}]
    print("CHECK-INS")
    analyze_time_series(ti_series_df, bootstrap)  # check-ins
    print("CHECK-OUTS")
    analyze_time_series(to_series_df, bootstrap)  # check-outs


def analysis():
    """
    1: Portal El Dorado
    6: Virrey
    8: Mazurén
    9: San Mateo
    10: Portal Sur
    11: Santa Isabel
    14: Escuela Militar
    18: Museo Nacional
    20: El Tiempo
    21: Portal El Tunal
    22: General Santander
    25: Calle 57
    29: Suba Calle 100
    """

    # analysis params
    TIME_MIN = 400
    TIME_MAX = 2300
    WINDOW_MINUTES = 15
    # STATION_IDS = [1, 6, 8, 9, 10, 11, 14, 18, 20, 21, 22, 25, 29]
    # PLOT_STATION_IDS = [1, 8, 9, 10, 11, 14, 18, 20, 21, 22, 25]
    STATION_IDS = [9]
    # PLOT_STATION_IDS = [9]
    # SEED_BOOTSTRAP_SG_TIME_SERIES is another param

    START_DATE = date(2025, 1, 1)
    END_DATE = date(2025, 12, 31)
    STRATUM_SIZE = 12

    DATES, _ = sample_dates(
        start_date=START_DATE,
        end_date=END_DATE,
        n=STRATUM_SIZE,
    )

    """
    params_dict = {
        "time_min": TIME_MIN,
        "time_max": TIME_MAX,
        "window_minutes": WINDOW_MINUTES,
        "station_ids": STATION_IDS,
        "seed": SEED_BOOTSTRAP_SG_TIME_SERIES,
    }
    """

    # _, _ = hash_params(params_dict)

    # station_ids=,
    counts_df = load_counts(
        time_min=TIME_MIN,
        time_max=TIME_MAX,
        station_ids=STATION_IDS,
        dates=DATES,
        window_minutes=WINDOW_MINUTES,
    )
    print("counts:", len(counts_df))

    station_groups = counts_df.groupby("station_id")

    for _, station_df in station_groups:
        # _, _, _ = get_station_details(station_df)

        analyze_station(station_df, bootstrap=True)


if __name__ == "__main__":
    analysis()
