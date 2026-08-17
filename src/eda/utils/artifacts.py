from pandas import DataFrame


def sg_r_ci_table_ins(_sg_r_ci_table_ins):
    df = DataFrame(
        [
            {
                "station_id": r[0],
                "station_code": r[1],
                "station_name": r[2],
                "day_type": r[3],
                "R_obs": round(r[4], 5),
                "q_025": round(r[5], 5),
                "q_975": round(r[6], 5),
            }
            for r in _sg_r_ci_table_ins
        ]
    )
    df.to_csv("artifacts/eda/day_type/sg_r_ci_table_ins.csv")


def sg_r_ci_table_outs(_sg_r_ci_table_outs):
    df = DataFrame(
        [
            {
                "station_id": r[0],
                "station_code": r[1],
                "station_name": r[2],
                "day_type": r[3],
                "R_obs": round(r[4], 5),
                "q_025": round(r[5], 5),
                "q_975": round(r[6], 5),
            }
            for r in _sg_r_ci_table_outs
        ]
    )
    df.to_csv("artifacts/eda/day_type/sg_r_ci_table_outs.csv")
