"""
Booking simulator: who gets the slot under fastest-finger (FCFS) vs declared-interest allocation?

`simulate` runs one Monte Carlo trial and returns raw outcomes; metrics.py turns them into numbers.
Mechanisms:
  fcfs     fastest finger first (bots are near-instant, humans are slower, connection latency persists)
  lottery  declared-interest window, uniform random draw
  fair     declared-interest window, weighted draw with fairness credits (allocator.py)
"""
import numpy as np

from allocator import draw_order, fairness_weights

N = 200                 # residents
S = 12                  # slots released per day
PRIME = 4               # of which are prime-time (more valuable)
DAYS = 60               # simulated days
VIGILANT_P = 0.15       # share of humans who are on the app when the window opens


def make_population(rng):
    p_want = 0.03 + 0.5 * rng.beta(2, 4, N)            # how often each person wants a slot
    base_lat = rng.lognormal(np.log(0.08), 0.6, N)     # persistent connection latency (s)
    vigilant = rng.random(N) < VIGILANT_P
    value = np.array([1.0] * PRIME + [0.55] * (S - PRIME))
    util = value + rng.normal(0, 0.15, (N, S))         # personal utility of each slot
    return p_want, base_lat, vigilant, util


def arrival_times(rng, base_lat, vigilant, is_bot):
    """Seconds after the window opens at which each person's request lands."""
    human = np.where(vigilant,
                     rng.lognormal(np.log(1.5), 0.4, N),   # sitting on the app
                     rng.exponential(1200, N)) + base_lat  # notices ~20 min later
    bot = base_lat + rng.exponential(0.02, N)              # near-instant, tiny jitter
    return np.where(is_bot, bot, human)


def simulate(mech, bot_frac, seed):
    rng = np.random.default_rng(seed)
    p_want, base_lat, vig, util = make_population(rng)
    is_bot = rng.random(N) < bot_frac
    wants, wins, arr_sum = np.zeros(N), np.zeros(N), np.zeros(N)
    streak = np.zeros(N)   # consecutive lost days while wanting
    rw = np.zeros(N)       # decayed recent wins
    util_sum = 0.0

    for _ in range(DAYS):
        want = rng.random(N) < p_want
        arr = arrival_times(rng, base_lat, vig, is_bot)
        arr_sum += arr
        idx = np.flatnonzero(want)

        if mech == "fcfs":                     # fastest finger first
            order = idx[np.argsort(arr[idx])]
        else:                                  # declared-interest window -> weighted draw
            if mech == "lottery":
                w = np.ones(len(idx))
            else:                              # fair: losers gain odds, recent winners lose odds
                w = fairness_weights(streak[idx], rw[idx])
            order = idx[draw_order(rng, w)]    # shared with allocator.py

        avail = np.ones(S, bool)
        won = np.zeros(N, bool)
        for u in order:                        # each picks their best remaining slot
            if not avail.any():
                break
            j = int(np.argmax(np.where(avail, util[u], -np.inf)))
            avail[j] = False
            won[u] = True
            util_sum += util[u, j]

        wants += want
        wins += won
        streak = np.where(want & ~won, streak + 1, np.where(won, 0, streak))
        rw = rw * 0.9 + won

    return dict(wants=wants, wins=wins, arr_sum=arr_sum, is_bot=is_bot, util_sum=util_sum)
