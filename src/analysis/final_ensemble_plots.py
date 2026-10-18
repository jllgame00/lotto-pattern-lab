"""Deterministic H16/H17 diagnostics from completed evaluation artifacts only."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd


ENSEMBLES = ("EqualAll", "OrdinarySubset", "DiversitySubset", "WeightedWinner", "SelectedEnsemble")
SCOPES = ("development", "validation", "final")
COLORS = ("#187b9d", "#d07832", "#7757a6", "#3b936b", "#c64e63")


def diagnostics(directory):
    """Read report CSV/JSON files and return twelve relative PNG paths.

    All figures display already-computed values. This function does not select
    models, recompute inference, consume draw data, or modify input artifacts.
    Existing diagnostic images are reproducibly replaced on a subsequent call.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(directory)
    performance = pd.read_csv(directory / "performance.csv")
    diversity = pd.read_csv(directory / "diversity.csv")
    grid = pd.read_csv(directory / "development_grid.csv")
    placebos = pd.read_csv(directory / "placebos.csv")
    leaveout = pd.read_csv(directory / "leave_one_out.csv")
    portfolios = pd.read_csv(directory / "portfolio_summary.csv")
    main = json.loads((directory / "main_summary.json").read_text(encoding="utf-8"))
    output = directory / "plots"
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    best_single = main["best_single"]
    if isinstance(best_single, dict):
        best_single = best_single.get("model", best_single.get("name", str(best_single)))
    selected = main.get("selected", {})
    selected_id = selected.get("id") if isinstance(selected, dict) else selected
    selected_gain = main.get("selected_final_rank_gain")

    def save(fig, name):
        fig.savefig(output / name, dpi=150, facecolor="white")
        plt.close(fig)
        paths.append(f"plots/{name}")

    def label_axes(ax, *, title, xlabel=None, ylabel=None):
        ax.set_title(title, fontsize=11, fontweight="semibold", pad=10)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#dfe4e8", linewidth=.6, alpha=.7)
        ax.set_axisbelow(True)

    def scope_values(frame, scope):
        aliases = (scope, "dev") if scope == "development" else (scope,)
        return frame[frame.scope.isin(aliases)]

    def bars_by_scope(frame, models, metric, title, name, label):
        fig, axes = plt.subplots(1, 3, figsize=(15, max(5, .43 * len(models) + 1.5)),
                                 sharey=True, layout="constrained")
        y = np.arange(len(models))
        for i, (scope, ax) in enumerate(zip(SCOPES, axes)):
            values = scope_values(frame, scope).set_index("model")[metric].reindex(models)
            colors = [COLORS[3] if model == "SelectedEnsemble" else COLORS[i] for model in models]
            ax.barh(y, values, color=colors, alpha=.88)
            ax.set_yticks(y, models, fontsize=9)
            label_axes(ax, title=scope.title(), xlabel=label)
            for index, value in enumerate(values):
                if np.isfinite(value):
                    ax.annotate(f"{value:.3f}", (value, index), xytext=(4, 0),
                                textcoords="offset points", va="center", fontsize=8)
            ax.margins(x=.2)
        axes[0].invert_yaxis()
        fig.suptitle(title, fontsize=15, fontweight="semibold")
        save(fig, name)

    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 11, "savefig.bbox": "tight"}):
        singles = [model for model in performance.model.drop_duplicates() if model not in ENSEMBLES]
        bars_by_scope(performance, singles, "avg_top6", "Candidate performance across chronological periods",
                      "01_candidate_performance.png", "Mean Top-6 hits (higher is better)")

        def pairwise_plot(metric, title, filename, low, high, diagonal, cmap):
            names = list(dict.fromkeys([*diversity.left.tolist(), *diversity.right.tolist()]))
            fig, axes = plt.subplots(2, 2, figsize=(13, 11), layout="constrained")
            for scope, ax in zip(("common", "development", "validation", "final"), axes.flat):
                matrix = np.full((len(names), len(names)), np.nan)
                np.fill_diagonal(matrix, diagonal)
                for row in scope_values(diversity, scope).itertuples(index=False):
                    i, j = names.index(row.left), names.index(row.right)
                    matrix[i, j] = matrix[j, i] = getattr(row, metric)
                im = ax.imshow(matrix, vmin=low, vmax=high, cmap=cmap)
                ax.set_xticks(range(len(names)), names, rotation=35, ha="right", fontsize=8)
                ax.set_yticks(range(len(names)), names, fontsize=8)
                ax.set_title(scope.title())
                for i in range(len(names)):
                    for j in range(len(names)):
                        value = matrix[i, j]
                        if np.isfinite(value):
                            color = "white" if (value - low) / (high - low) > .75 else "#202830"
                            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8, color=color)
            fig.colorbar(im, ax=axes.ravel().tolist(), shrink=.8, label=title)
            fig.suptitle(f"{title}: candidate-pair diagnostics", fontsize=15)
            save(fig, filename)

        pairwise_plot("spearman", "Ranking Spearman correlation", "02_spearman.png", -1, 1, 1, "coolwarm")
        pairwise_plot("top6_overlap", "Top-6 overlap (number count)", "03_top6_overlap.png",
                      0, 6, 6, "Blues")

        compare_models = list(dict.fromkeys([best_single, *ENSEMBLES]))
        compare_models = [name for name in compare_models if name in set(performance.model)]
        bars_by_scope(performance, compare_models, "avg_top6", "Single and ensemble performance: three held periods",
                      "04_three_way_performance.png", "Mean Top-6 hits (higher is better)")

        fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
        positions = grid["size"].to_numpy(float)
        # Fixed offsets make coincident grid rows visible without random jitter.
        offsets = ((np.arange(len(grid)) % 17) - 8) * .012
        for ax, metric, label in zip(axes, ("avg_top6", "mean_winning_rank"),
                                     ("Mean Top-6 hits (higher is better)", "Mean winning-number rank (lower is better)")):
            points = ax.scatter(positions + offsets, grid[metric], c=grid.diversity_objective,
                                cmap="viridis", s=20, alpha=.6)
            selected_rows = grid[grid.id.astype(str).eq(str(selected_id))]
            if len(selected_rows):
                ax.scatter(selected_rows["size"], selected_rows[metric], marker="*", s=180,
                           color=COLORS[4], edgecolor="black", label="Frozen selection", zorder=5)
                ax.legend(fontsize=8)
            ax.set_xticks(sorted(grid["size"].unique()))
            label_axes(ax, title=label, xlabel="Active candidates in development grid", ylabel=label)
        fig.colorbar(points, ax=axes.ravel().tolist(), label="Stored diversity objective", shrink=.8)
        fig.suptitle("Development subset inventory: every evaluated grid row", fontsize=15)
        save(fig, "05_subset_inventory.png")

        fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
        equal = grid["equal"].astype(str).str.lower().isin(("true", "1", "1.0"))
        for flag, label, color in ((True, "Equal weights", COLORS[0]), (False, "Nonuniform weights", COLORS[1])):
            subset = grid[equal.eq(flag)]
            axes[0].scatter(subset.redundancy, subset.normalized_loss, label=label,
                            s=18, alpha=.55, color=color)
        axes[0].legend(fontsize=9)
        label_axes(axes[0], title="Fixed weight-template inventory", xlabel="Stored redundancy",
                   ylabel="Stored normalized development loss")
        weights = selected.get("weights", {}) if isinstance(selected, dict) else {}
        if not weights:
            selected_rows = grid[grid.id.astype(str).eq(str(selected_id))]
            if len(selected_rows):
                weights = selected_rows.iloc[0].weights
        if isinstance(weights, str):
            try:
                weights = json.loads(weights)
            except json.JSONDecodeError:
                weights = ast.literal_eval(weights)
        if isinstance(weights, dict):
            weight_names, weight_values = list(weights), list(weights.values())
        else:
            weight_values = list(weights)
            weight_names = ["GapLogistic", "GraphStructureModel", "GapShapeModel", "MirrorModel"]
        axes[1].barh(weight_names, weight_values, color=COLORS[3])
        axes[1].invert_yaxis()
        label_axes(axes[1], title=f"Frozen selected weights: {selected_id}", xlabel="Weight")
        fig.suptitle("Weight templates and frozen selected allocation", fontsize=15)
        save(fig, "06_weight_templates.png")

        def placebo_plot(kind, title, filename):
            subset = placebos[placebos.kind.eq(kind)]
            fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
            finite = subset.final_rank_gain.dropna().to_numpy(float)
            if len(finite):
                axes[0].hist(finite, bins=25, color=COLORS[0], alpha=.8, edgecolor="white")
            if selected_gain is not None and np.isfinite(float(selected_gain)):
                axes[0].axvline(float(selected_gain), color=COLORS[4], linewidth=2,
                                label=f"Selected ensemble: {float(selected_gain):.3f}")
                axes[0].legend(fontsize=9)
            label_axes(axes[0], title="Final-period rank gain distribution",
                       xlabel="Gain over best single (positive is better)", ylabel="Construction replicates")
            passed = subset.gate_passed.astype(str).str.lower().isin(("true", "1", "1.0"))
            for flag, label, color in ((False, "Gate failed", "#a3adb7"), (True, "Gate passed", COLORS[3])):
                part = subset[passed.eq(flag)]
                axes[1].scatter(part.development_rank_gain, part.validation_rank_gain,
                                s=18, alpha=.6, color=color, label=f"{label}: {len(part)}")
            axes[1].axhline(0, color="#697680", linewidth=.8)
            axes[1].axvline(0, color="#697680", linewidth=.8)
            axes[1].legend(fontsize=9)
            label_axes(axes[1], title="Development and validation gains",
                       xlabel="Development rank gain", ylabel="Validation rank gain")
            fig.suptitle(title, fontsize=15)
            save(fig, filename)

        placebo_plot("random_weight", "Random-weight placebo audit", "07_random_weight_placebo.png")
        placebo_plot("random_candidate", "Random-candidate placebo audit", "08_random_candidate_placebo.png")

        final = scope_values(performance, "final").set_index("model")
        fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
        for ax, metric, title in zip(axes, ("avg_top6", "mean_winning_rank"),
                                    ("Mean Top-6 hits: higher is better", "Mean winning-number rank: lower is better")):
            values = final[metric].reindex(compare_models)
            ax.barh(compare_models, values, color=[COLORS[3] if m == "SelectedEnsemble" else COLORS[0]
                                                 for m in compare_models])
            ax.invert_yaxis()
            label_axes(ax, title=title, xlabel=metric)
            for index, value in enumerate(values):
                if np.isfinite(value):
                    ax.annotate(f"{value:.3f}", (value, index), xytext=(4, 0), textcoords="offset points",
                                va="center", fontsize=9)
            ax.margins(x=.2)
        fig.suptitle(f"Historical final: ensemble versus frozen best single ({best_single})", fontsize=15)
        save(fig, "09_final_ensemble_vs_single.png")

        fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
        removed = leaveout.removed.drop_duplicates().tolist()
        for ax, metric, title in zip(axes, ("top6_change", "winner_rank_change"),
                                    ("Top-6 hit change (positive is better)", "Winning-rank change (negative is better)")):
            for i, scope in enumerate(SCOPES):
                values = scope_values(leaveout, scope).set_index("removed")[metric].reindex(removed)
                ax.plot(np.arange(len(removed)), values, "o-", label=scope.title(), color=COLORS[i])
            ax.set_xticks(np.arange(len(removed)), removed, rotation=25, ha="right", fontsize=9)
            ax.axhline(0, color="#697680", linewidth=.8)
            label_axes(ax, title=title, xlabel="Removed candidate", ylabel="Change from full selected ensemble")
        axes[1].legend(fontsize=9)
        fig.suptitle("Leave-one-candidate-out sensitivity", fontsize=15)
        save(fig, "10_leave_one_out.png")

        fig, ax = plt.subplots(figsize=(11, 6), layout="constrained")
        for i, model in enumerate(compare_models):
            values = [scope_values(performance, scope).set_index("model").mean_winning_rank.get(model, np.nan)
                      for scope in SCOPES]
            ax.plot(SCOPES, values, marker="o", label=model, color=COLORS[i % len(COLORS)],
                    linewidth=2.6 if model == "SelectedEnsemble" else 1.3,
                    linestyle="--" if model == best_single else "-")
        label_axes(ax, title="Winning-number rank across chronological periods",
                   ylabel="Mean winning-number rank (lower is better)")
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
        save(fig, "11_winning_rank.png")

        fig, axes = plt.subplots(1, 3, figsize=(16, 5), layout="constrained")
        for i, (method, group) in enumerate(portfolios.groupby("method", sort=False)):
            group = group.sort_values("budget")
            color = COLORS[i % len(COLORS)]
            axes[0].plot(group.budget, group.mean_best_main, "o-", label=method, color=color)
            for ax, event in zip(axes[1:], ("ge4", "ge5")):
                average = group[f"{event}_mean_count"].to_numpy(float)
                lower = average - group[f"{event}_min_count"].to_numpy(float)
                upper = group[f"{event}_max_count"].to_numpy(float) - average
                ax.errorbar(group.budget, average, yerr=np.stack([lower, upper]),
                            fmt="o-", color=color, capsize=3, alpha=.85)
        for ax, title, ylabel in zip(axes, ("Best main-number matches", "Targets with at least four matches", "Targets with at least five matches"),
                                    ("Mean best main matches", "Mean event count across seeds", "Mean event count across seeds")):
            label_axes(ax, title=title, xlabel="Tickets per historical target", ylabel=ylabel)
            ax.set_xticks((1, 5, 10, 20))
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=3, fontsize=9)
        fig.suptitle("Equal-budget portfolios; error bars show construction-seed min/max counts", fontsize=15)
        save(fig, "12_portfolios.png")
    return paths
