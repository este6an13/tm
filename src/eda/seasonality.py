from datetime import date
from itertools import combinations

from numpy import concatenate, quantile
from numpy.random import default_rng
from scipy.spatial.distance import cdist, pdist

from src.data.load import load_counts
from src.data.sampling.dates import sample_dates
from src.eda.utils import TIME_SERIES_PREFIX_COLS, station_time_series
from src.utils.seeds import SEED_BOOTSTRAP_SG_TIME_SERIES
from src.utils.day_types import DAY_TYPES

BOOTSTRAP_ITER = 5000

rng = default_rng(SEED_BOOTSTRAP_SG_TIME_SERIES)

MONTHS = range(1, 13)
MONTHS_PAIRS = list(combinations(MONTHS, 2))


# sample N rows with replacement
def sample_with_replacement(arr):
    N = len(arr)
    idx = rng.choice(range(N), N)
    return arr[idx]


def station_months_matrices(day_type_df, bootstrap=False):
    sm_matrices = {}
    for month, month_df in day_type_df.groupby("month"):
        matrix = month_df.drop(columns=TIME_SERIES_PREFIX_COLS).values
        sm_matrices[month] = sample_with_replacement(matrix) if bootstrap else matrix
    return sm_matrices


def within_months_analysis(sm_matrices):
    dist_arrays = {}
    means = {}
    for m in MONTHS:
        dist_array = pdist(sm_matrices[m], metric="euclidean")
        mean = dist_array.mean()  # already excludes diagonal
        means[m] = mean
        dist_arrays[m] = dist_array
    return means, dist_arrays


def between_months_analysis(sm_matrices):
    dist_arrays = {}
    for q1, q2 in MONTHS_PAIRS:
        pair_dist_matrix = cdist(sm_matrices[q1], sm_matrices[q2], metric="euclidean")
        pair_dist_array = pair_dist_matrix.ravel()  # 1D to concatenate
        dist_arrays[(q1, q2)] = pair_dist_array

    dist_matrix = concatenate(list(dist_arrays.values()))
    return dist_matrix.mean(), dist_arrays


def _analyze_time_series(t_series_df, bootstrap=False):
    sm_matrices = station_months_matrices(t_series_df, bootstrap)
    w_means, w_dists = within_months_analysis(sm_matrices)
    b_mean, b_dists = between_months_analysis(sm_matrices)
    res = []
    for month, w_mean in w_means.items():
        R = b_mean / w_mean
        res.append((month, R))
    return res, w_dists, b_dists


def repeat_time_series_analysis(t_series_df):
    results = {}
    intervals = {}
    for _ in range(BOOTSTRAP_ITER):
        # perform 1 bootstrap iteration
        partial_result, _, _ = _analyze_time_series(t_series_df, bootstrap=True)
        # aggregate results
        for month, R in partial_result:
            results.setdefault(month, []).append(R)

    # compute CI per day_type
    for month, arr in results.items():
        q025, q975 = quantile(arr, [0.025, 0.975])
        intervals[month] = (q025, q975)

    return intervals


def analyze_time_series(t_series_df, bootstrap=False, day_types=DAY_TYPES):
    for day_type, day_type_df in t_series_df.groupby("day_type"):
        if day_type not in day_types:
            continue
        obs, _, _ = _analyze_time_series(day_type_df)
        if bootstrap:
            intervals = repeat_time_series_analysis(day_type_df)

        # organize results
        results = {}
        for month, R in obs:
            key = (day_type, month)
            results[key] = (R, intervals[month])
            print(
                day_type,
                month,
                round(R, 5),
                f"({round(intervals[month][0], 5)}, {round(intervals[month][1], 5)})",
            )
        print()
    print()


def analyze_station(station_df, bootstrap=False, day_types=DAY_TYPES):
    ti_series_df, to_series_df = station_time_series(station_df)
    # dists shapes are nested: [{q1: w1, ...} {p1: b1, ...}]
    print("CHECK-INS")
    analyze_time_series(ti_series_df, bootstrap, day_types=day_types)  # check-ins
    print("CHECK-OUTS")
    analyze_time_series(to_series_df, bootstrap, day_types=day_types)  # check-outs


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
    STATION_IDS = [6]
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

    DAY_TYPES_OVERRIDE = ["WD"]  # I'm only interested in analyzing seasonality in WD

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

        analyze_station(station_df, bootstrap=True, day_types=DAY_TYPES_OVERRIDE)


if __name__ == "__main__":
    analysis()
