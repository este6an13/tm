from numpy import concatenate

TIME_SERIES_PREFIX_COLS = ["year", "month", "day", "day_type", "day_of_week"]


def time_series_columns(station_df):
    ti_cols = [col for col in station_df.columns if col.startswith("ti_")]
    to_cols = [col for col in station_df.columns if col.startswith("to_")]
    return ti_cols, to_cols


def _station_time_series(station_df):
    ti_cols, to_cols = time_series_columns(station_df)
    ti_series = station_df[TIME_SERIES_PREFIX_COLS + ti_cols]
    to_series = station_df[TIME_SERIES_PREFIX_COLS + to_cols]
    ti_series = ti_series.fillna(0)
    to_series = to_series.fillna(0)
    return ti_series, to_series


def station_time_series(station_df):
    return _station_time_series(station_df)


def station_median_profile(station_df):
    ti_cols, to_cols = time_series_columns(station_df)
    ti_series, to_series = _station_time_series(station_df)
    ti_profile = ti_series[ti_cols].median(axis=0).values
    to_profile = to_series[to_cols].median(axis=0).values
    return ti_profile, to_profile


def station_normalized_profile(station_df):
    ti_profile, to_profile = station_median_profile(station_df)
    ti_volume, to_volume = ti_profile.sum(), to_profile.sum()
    vector = concatenate([ti_profile / ti_volume, to_profile / to_volume])
    return vector


def get_station_details(station_df):
    station_id = station_df.iloc[0]["station_id"]
    station_code = station_df.iloc[0]["station_code"]
    station_name = station_df.iloc[0]["station_name"]
    return station_id, station_code, station_name
