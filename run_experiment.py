#!/usr/bin/env python3
"""Reproduce every number and chart in the README.   Usage: python run_experiment.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experiments import ADOPTION, SCENARIOS, run_scenarios, run_sweep
from simulator import DAYS, N, S

OUT = Path(__file__).parent / "results"
RED, GREEN, GREY = "#c0392b", "#1e8449", "#7f8c8d"


def write_table(res):
    hdr = ("| Scenario | Demand served | Gini (win-rate) | Shut-out rate | Fast-quintile win % | "
           "Slow-quintile win % | Vigilance min/mo | Slot utility |\n|---|---|---|---|---|---|---|---|\n")
    rows = "".join(
        f"| {k} | {r['served']:.0%} | {r['gini']:.2f} | {r['shutout']:.0%} | {r['fast_rate']:.0%} | "
        f"{r['slow_rate']:.0%} | {r['vigil_min']:.0f} | {r['welfare']:.2f} |\n" for k, r in res.items())
    (OUT / "results.md").write_text(hdr + rows)
    print(hdr + rows)


def chart_mechanism_comparison(res):
    labels = [s[0] for s in SCENARIOS]
    keys = [k.replace("\n", " ") for k in labels]
    colors = [RED, RED, RED, GREY, GREEN, GREEN]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    ax[0, 0].bar(x, [res[k]["gini"] for k in keys], color=colors)
    ax[0, 0].set_title("Inequality of access (Gini of win-rate, lower = fairer)")
    ax[0, 1].bar(x, [res[k]["shutout"] * 100 for k in keys], color=colors)
    ax[0, 1].set_title("% of active residents who NEVER got a slot in 60 days")
    w = 0.38
    ax[1, 0].bar(x - w / 2, [res[k]["fast_rate"] * 100 for k in keys], w, color=colors)
    ax[1, 0].bar(x + w / 2, [res[k]["slow_rate"] * 100 for k in keys], w, color=colors, alpha=0.4)
    ax[1, 0].set_title("Win rate: fastest vs slowest fifth (solid vs faded)")
    ax[1, 0].set_ylabel("% of requests that got a slot")
    ax[1, 1].bar(x, [res[k]["vigil_min"] for k in keys], color=colors)
    ax[1, 1].set_title("Manual vigilance (minutes per resident per month)")
    for a in ax.ravel():
        a.set_xticks(x)
        a.set_xticklabels(labels, fontsize=8)
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Fastest-finger vs fair allocation: {N} residents, {S} slots/day, {DAYS} days", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "mechanism_comparison.png", dpi=160)
    plt.close(fig)


def chart_fairness_vs_bot_adoption(sweep):
    fig, ax = plt.subplots(figsize=(8, 5))
    for m, c, name in (("fcfs", RED, "FCFS"), ("fair", GREEN, "Fair allocator")):
        ax.plot(ADOPTION, [r["bot_rate"] * 100 for r in sweep[m]], color=c, marker="o", label=f"{name}: bot users")
        ax.plot(ADOPTION, [r["human_rate"] * 100 for r in sweep[m]], color=c, marker="s", ls="--",
                label=f"{name}: manual users")
    ax.set_xlabel("Share of residents running a fast bot")
    ax.set_ylabel("Win rate (% of requests that got a slot)")
    ax.set_title("Speed pays under FCFS; under the allocator it doesn't")
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fairness_vs_bot_adoption.png", dpi=160)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    res = run_scenarios()
    (OUT / "results.json").write_text(json.dumps(res, indent=2))
    write_table(res)
    chart_mechanism_comparison(res)
    sweep = run_sweep()
    (OUT / "sweep.json").write_text(json.dumps(sweep, indent=2))
    chart_fairness_vs_bot_adoption(sweep)
    print("Arms-race sweep (adoption, bot win %, manual win %):")
    for m in ("fcfs", "fair"):
        print(m, [(a, round(r["bot_rate"] * 100), round(r["human_rate"] * 100)) for a, r in zip(ADOPTION, sweep[m])])
    print(f"\nWrote results to {OUT}")


if __name__ == "__main__":
    main()
