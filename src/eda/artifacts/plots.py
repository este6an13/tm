import matplotlib.pyplot as plt
from numpy import clip, inf, median, percentile
from numpy.random import default_rng
from pandas import Index

from src.eda.artifacts.load import load_sg_r_ci_tables
from src.eda.artifacts.utils import record_artifact
from src.eda.utils import station_time_series
from src.utils.day_types import DAY_TYPES
from src.utils.plotting import DAY_TYPES_COLORS


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


def _make_sg_profile_plot(
    time_cols, ins_curves, outs_curves, station_id, station_code, station_name
):
    fig, (ax_in, ax_out) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    X = list(map(time_int_to_min, time_cols))

    for ax, curves, ylabel in (
        (ax_in, ins_curves, "check-ins per 15 min"),
        (ax_out, outs_curves, "check-outs per 15 min"),
    ):
        for day_type in DAY_TYPES:
            med, q25, q75, n = curves[day_type]
            color = DAY_TYPES_COLORS[day_type]
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

    fig.suptitle(
        f"Daily demand profiles by day type: {station_id}:{station_code} - {station_name}",
        fontsize=14,
        fontweight="bold",
    )
    ax_in.set_title("Check-ins", fontsize=11, loc="left")
    ax_out.set_title("Check-outs", fontsize=11, loc="left")

    fig.text(
        0.5,
        0.945,
        "median and interquartile range across days",
        ha="center",
        fontsize=10,
        color="0.4",
    )

    ax_in.legend(frameon=False)
    fig.tight_layout()

    return fig


# 1 plot per station (2 panels: ins/outs), 3 curves (1 per day type)
def sg_profile_plot(station_df, params_str, params_hash):
    station_id = station_df.iloc[0]["station_id"]
    station_code = station_df.iloc[0]["station_code"]
    station_name = station_df.iloc[0]["station_name"]

    # time_cols will define the horizontal axis
    time_cols = get_time_cols(station_df.columns)

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

    # generate plot
    fig = _make_sg_profile_plot(
        time_cols, ti_curves, to_curves, station_id, station_code, station_name
    )

    # persist artifact
    fig.savefig(
        f"artifacts/eda/day_type/{params_hash[:7]}_{station_id}_sg_profile_plot.jpg",
        dpi=200,
        bbox_inches="tight",
    )
    record_artifact(f"{station_id}_sg_profile_plot", params_str, params_hash)


def _make_sg_r_ci_plot(df, order, pos):
    fig, axes = plt.subplots(
        2,
        len(DAY_TYPES),
        figsize=(12, 2 + 0.28 * len(order)),
        sharex=True,
        sharey=True,
        layout="constrained",
    )

    # first check-ins, then check-outs
    for row, direction in enumerate(("ins", "outs")):
        # per day type
        for col, day_type in enumerate(DAY_TYPES):
            ax = axes[row, col]
            # one panel per (direction, day_type) combination
            panel = df[(df.day_type == day_type) & (df.direction == direction)]

            ax.axvline(1.0, ls="--", lw=1, color="red", alpha=0.5, zorder=0)

            # a record is a (station, day type) combination
            for r in panel.itertuples():
                # we extract the values/statistics
                y = pos[r.station_name]
                supported = r.q_025 > 1
                color = DAY_TYPES_COLORS[day_type] if supported else "0.35"
                ax.hlines(y, r.q_025, r.q_975, color=color, lw=2)
                ax.plot(r.R_obs, y, "o", ms=5, color=color)

            # presentation
            p = (panel.q_025 > 1).mean()
            ax.text(
                0.97,
                0.02,
                f"p = {p:.2f}",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9,
                color="0.4",
            )

            if row == 0:
                ax.set_title(day_type)
            ax.spines[["top", "right"]].set_visible(False)

    # more presentation
    axes[0, 0].set_yticks(range(len(order)))
    axes[0, 0].set_yticklabels(order, fontsize=8)
    axes[1, 0].set_yticklabels(order, fontsize=8)
    axes[0, 0].invert_yaxis()

    for col in range(len(DAY_TYPES)):
        axes[1, col].set_xlabel("R = between / within")

    axes[0, 0].set_ylabel("check-ins")
    axes[1, 0].set_ylabel("check-outs")

    fig.suptitle("Day-type separation by station", fontsize=14, fontweight="bold")

    return fig


def sg_r_ci_plot(params_str, params_hash):
    df = load_sg_r_ci_tables(params_hash)

    # prepare prerrequisites for plot: order of stations and pos indexes
    ref = df[(df.day_type == "WD") & (df.direction == "ins")]
    # we just want to show one CI per station in desc order, in each panel
    order = ref.sort_values("R_obs", ascending=False)["station_name"].tolist()
    pos = {name: i for i, name in enumerate(order)}

    # make plot
    fig = _make_sg_r_ci_plot(df, order, pos)

    # artifact persistence
    fig.savefig(
        f"artifacts/eda/day_type/{params_hash[:7]}_sg_r_ci_plot.jpg",
        dpi=200,
        bbox_inches="tight",
    )
    record_artifact("sg_r_ci_plot", params_str, params_hash)


rng_plot = default_rng(42)


def sg_dists_clouds_plot(
    station_id,
    station_code,
    station_name,
    params_str,
    params_hash,
    withins,
    betweens,
    direction,
):
    groups = []

    for g in DAY_TYPES:
        groups.append((f"within {g}", withins[g], DAY_TYPES_COLORS[g]))
    for (g1, g2), arr in betweens.items():
        groups.append((f"{g1} ↔ {g2}", arr, "0.45"))

    pos = [0, 1, 2, 4, 5, 6]  # a gap at idx 3 to separate between from within sections

    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")

    for (_, arr, color), y in zip(groups, pos):
        # cloud plotting
        parts = ax.violinplot(
            arr,
            positions=[y],
            vert=False,
            widths=0.9,
            showextrema=False,
            showmedians=False,
        )
        for body in parts["bodies"]:
            v = body.get_paths()[0].vertices
            v[:, 1] = clip(v[:, 1], y, inf)
            body.set_facecolor(color)
            body.set_alpha(0.5)

        # rain plottinh
        jitter = rng_plot.uniform(-0.13, -0.03, size=len(arr))
        ax.scatter(arr, y + jitter, s=3, color=color, alpha=0.25, linewidths=0)

        # median + IQR interval
        q25, med, q75 = percentile(arr, [25, 50, 75])
        ax.hlines(y - 0.18, q25, q75, color="0.2", lw=2)
        ax.plot(
            med, y - 0.18, "o", ms=4, color="white", markeredgecolor="0.2", zorder=3
        )

    ax.set_yticks(pos)
    ax.set_yticklabels([label for label, _, _ in groups])
    ax.set_xlabel("pairwise Euclidean distance between days")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    fig.suptitle(
        f"Within- vs between-day-type distances: {station_code} - {station_name} - {direction}",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(
        f"artifacts/eda/day_type/{params_hash[:7]}_{station_id}_{direction}_sg_dists_clouds_plot.jpg",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)
