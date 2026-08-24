TIME_SERIES_PREFIX_COLS = ["year", "month", "day", "day_type"]


def station_time_series(station_df):
    ti_cols = [col for col in station_df.columns if col.startswith("ti_")]
    to_cols = [col for col in station_df.columns if col.startswith("to_")]
    ti_series = station_df[TIME_SERIES_PREFIX_COLS + ti_cols]
    to_series = station_df[TIME_SERIES_PREFIX_COLS + to_cols]
    ti_series = ti_series.fillna(0)
    to_series = to_series.fillna(0)
    return ti_series, to_series


def get_station_details(station_df):
    station_id = station_df.iloc[0]["station_id"]
    station_code = station_df.iloc[0]["station_code"]
    station_name = station_df.iloc[0]["station_name"]
    return station_id, station_code, station_name
