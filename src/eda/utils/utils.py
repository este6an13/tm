def station_time_series(station_df):
    ti_cols = [col for col in station_df.columns if col.startswith("ti_")]
    to_cols = [col for col in station_df.columns if col.startswith("to_")]
    ti_series = station_df[["day_type"] + ti_cols]
    to_series = station_df[["day_type"] + to_cols]
    ti_series = ti_series.fillna(0)
    to_series = to_series.fillna(0)
    return ti_series, to_series
