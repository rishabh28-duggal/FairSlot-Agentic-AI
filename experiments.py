"""Experiment definitions: the scenarios compared and the bot-adoption sweep."""
import warnings

import numpy as np

from metrics import compute_metrics
from simulator import simulate

SEEDS = 20   # Monte Carlo repetitions per scenario

# (label, mechanism, share of residents running a fast bot)
SCENARIOS = [
    ("FCFS\nmanual", "fcfs", 0.0),
    ("FCFS\n30% bots", "fcfs", 0.3),
    ("FCFS\n100% bots", "fcfs", 1.0),
    ("Lottery\nall agents", "lottery", 1.0),
    ("Fair alloc.\nall agents", "fair", 1.0),
    ("Fair alloc.\n30% hammer bots", "fair", 0.3),
]
ADOPTION = [0.05, 0.1, 0.25, 0.5, 0.75, 0.95]


def run(mech, bot_frac, seeds=SEEDS):
    runs = [compute_metrics(simulate(mech, bot_frac, s), mech) for s in range(seeds)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN groups (e.g. no bots) stay NaN
        return {k: float(np.nanmean([r[k] for r in runs])) for k in runs[0]}


def run_scenarios():
    return {label.replace("\n", " "): run(mech, bf) for label, mech, bf in SCENARIOS}


def run_sweep():
    return {m: [run(m, a) for a in ADOPTION] for m in ("fcfs", "fair")}
