from pandas import DataFrame

from src.eda.artifacts.utils import record_artifact


def sg_dist_matrix_anomalies(
    _sg_dist_matrix_anomalies, params_hash, params_str, station_id, direction
):
    df = DataFrame(
        [
            {
                "day_type": r[0],
                "date": r[1],
                "mean": r[2],
                "ratio": r[3],
            }
            for r in _sg_dist_matrix_anomalies
        ]
    )
    df.to_csv(
        f"artifacts/eda/day_type/{params_hash[:7]}_{station_id}_sg_dist_matrix_anomalies_{direction}.csv"
    )
    record_artifact(
        f"{station_id}_sg_dist_matrix_anomalies_{direction}", params_str, params_hash
    )


def sg_r_ci_table_ins(_sg_r_ci_table_ins, params_str, params_hash):
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
    df.to_csv(f"artifacts/eda/day_type/{params_hash[:7]}_sg_r_ci_table_ins.csv")
    record_artifact("sg_r_ci_table_ins", params_str, params_hash)


def sg_r_ci_table_outs(_sg_r_ci_table_outs, params_str, params_hash):
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
    df.to_csv(f"artifacts/eda/day_type/{params_hash[:7]}_sg_r_ci_table_outs.csv")
    record_artifact("sg_r_ci_table_outs", params_str, params_hash)


def g_mr_ci_p_table_ins(_g_mr_ci_p_table_ins, params_str, params_hash):
    df = DataFrame(
        [
            {
                "day_type": r[0],
                "median_R": round(r[1], 5),
                "q_25": round(r[2], 5),
                "q_75": round(r[3], 5),
                "p": round(r[4], 5),
            }
            for r in _g_mr_ci_p_table_ins
        ]
    )
    df.to_csv(f"artifacts/eda/day_type/{params_hash[:7]}_g_mr_ci_p_table_ins.csv")
    record_artifact("g_mr_ci_p_table_ins", params_str, params_hash)


def g_mr_ci_p_table_outs(_g_mr_ci_p_table_outs, params_str, params_hash):
    df = DataFrame(
        [
            {
                "day_type": r[0],
                "median_R": round(r[1], 5),
                "q_25": round(r[2], 5),
                "q_75": round(r[3], 5),
                "p": round(r[4], 5),
            }
            for r in _g_mr_ci_p_table_outs
        ]
    )
    df.to_csv(f"artifacts/eda/day_type/{params_hash[:7]}_g_mr_ci_p_table_outs.csv")
    record_artifact("g_mr_ci_p_table_outs", params_str, params_hash)
