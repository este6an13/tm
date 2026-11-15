from datetime import date

from numpy import vstack

from src.data.load import get_complete_dates, load_counts
from src.eda.utils import get_station_details, station_normalized_profile
from src.utils.hash import hash_params


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
    STATION_IDS = [6, 9, 10, 22]
    # PLOT_STATION_IDS = [1, 8, 9, 10, 11, 14, 18, 20, 21, 22, 25]
    # PLOT_STATION_IDS = [9]

    START_DATE = date(2025, 1, 1)
    END_DATE = date(2025, 12, 31)

    STATION_DATES = get_complete_dates(
        START_DATE, END_DATE, STATION_IDS, TIME_MIN, TIME_MAX, WINDOW_MINUTES
    )

    DAY_TYPES = ["WD"]

    params_dict = {
        "time_min": TIME_MIN,
        "time_max": TIME_MAX,
        "window_minutes": WINDOW_MINUTES,
        "station_ids": STATION_IDS,
        "day_types": DAY_TYPES,
    }

    _, params_hash = hash_params(params_dict)
    print(params_hash[:7])

    # station_ids=,
    counts_df = load_counts(
        time_min=TIME_MIN,
        time_max=TIME_MAX,
        station_ids=STATION_IDS,
        station_dates=STATION_DATES,
        window_minutes=WINDOW_MINUTES,
    )
    print("counts:", len(counts_df))

    station_groups = counts_df.groupby("station_id")

    for day_type in DAY_TYPES:
        vectors = []
        for _, station_df in station_groups:
            _, _, station_name = get_station_details(station_df)
            print(station_name)

            station_dt_df = station_df[station_df.day_type == day_type]

            station_dt_df = station_df[station_df.day_type == day_type]
            vector = station_normalized_profile(station_dt_df)
            vectors.append(vector)

        X = vstack(vectors)
        print(X.shape)
        print(X)


if __name__ == "__main__":
    analysis()
