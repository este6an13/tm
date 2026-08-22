from pathlib import Path

from pandas import concat, read_csv


def load_sg_r_ci_tables(params_hash):
    base = Path("artifacts/eda/day_type")
    frames = []
    for direction in ("ins", "outs"):
        df = read_csv(base / f"{params_hash[:7]}_sg_r_ci_table_{direction}.csv")
        df["direction"] = direction
        frames.append(df)
    return concat(frames, ignore_index=True)
