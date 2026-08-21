import matplotlib.pyplot as plt
from numpy import median, percentile
from pandas import Index

from src.eda.utils.utils import station_time_series
from src.utils.day_types import DAY_TYPES
from src.utils.plotting import DATE_TYPE_COLORS


# transform to absolute minutes to plot scaled correctly
# if treated as time_int, plot shows a longer jump when going from 445 to 500
# if transform we would have equidistant jumps: 285 -> 300
def time_int_to_min(time_int: int) -> int:
    return (time_int // 100) * 60 + time_int % 100


# transform time_int to time representation: 445 -> 04:45
def time_int_to_str(time_int: int) -> str:
    return f"{(time_int // 100):02d}:{(time_int % 100):02d}"


# in time int format: 400, 415, 430, ...
def get_time_cols(columns: Index):
    time_cols = sorted(
        [int(c.replace("ti_", "")) for c in list(columns) if c.startswith("ti_")]
    )
    return time_cols


def _plot(time_cols, ins_curves, outs_curves):
    fig, (ax_in, ax_out) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    X = list(map(time_int_to_min, time_cols))

    for ax, curves, ylabel in (
        (ax_in, ins_curves, "check-ins per 15 min"),
        (ax_out, outs_curves, "check-outs per 15 min"),
    ):
        for day_type in DAY_TYPES:
            med, q25, q75, n = curves[day_type]
            color = DATE_TYPE_COLORS[day_type]
            label = f"{day_type} (n={n})"
            ax.fill_between(
                X,
                q25,
                q75,
                color=color,
                alpha=0.2,
                linewidth=0,
                label=f"{label} envelope",
            )
            ax.plot(X, med, color=color, marker="o", lw=2, markersize=4, label=label)

        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)

    ax_range = range(time_cols[0] - time_cols[0] % 100, time_cols[-1] + 1, 100)
    ax_out.set_xticks(list(map(time_int_to_min, ax_range)))
    ax_out.set_xticklabels(list(map(time_int_to_str, ax_range)))
    ax_out.set_xlabel("time of day")
    ax_out.tick_params(rotation=45, rotation_mode="xtick")

    ax_in.legend(frameon=False)
    fig.tight_layout()
    fig.show()

    return fig


# 1 plot per station (2 panels: ins/outs), 3 curves (1 per day type)
def plot(counts_df, params_str, params_hash):
    # time_cols will define the horizontal axis
    time_cols = get_time_cols(counts_df.columns)  # universal for all stations

    station_groups = counts_df.groupby("station_id")
    for station_id, station_df in station_groups:
        # extract time series per station
        ti_series_df, to_series_df = station_time_series(station_df)

        # compute data to plot: envelopes
        # check-ins
        ti_curves = {}
        ti_g_groups = ti_series_df.groupby("day_type")
        for day_type, ti_g_group in ti_g_groups:
            ti_g_group_matrix = ti_g_group.drop(columns=["day_type"]).values
            med = median(ti_g_group_matrix, axis=0)
            q25, q75 = percentile(ti_g_group_matrix, [25, 75], axis=0)
            n = ti_g_group_matrix.shape[0]
            ti_curves[day_type] = (med, q25, q75, n)

        # check-outs
        to_curves = {}
        to_g_groups = to_series_df.groupby("day_type")
        for day_type, to_g_group in to_g_groups:
            to_g_group_matrix = to_g_group.drop(columns=["day_type"]).values
            med = median(to_g_group_matrix, axis=0)
            q25, q75 = percentile(to_g_group_matrix, [25, 75], axis=0)
            n = to_g_group_matrix.shape[0]
            to_curves[day_type] = (med, q25, q75, n)

        # actual plotting step per station
        fig = _plot(time_cols, ti_curves, to_curves)
        fig.savefig(
            f"artifacts/eda/day_type/{params_hash[:7]}_{station_id}_sg_profile_plot.jpg",
            dpi=200,
            bbox_inches="tight",
        )
