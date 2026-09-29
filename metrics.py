"""Metrics: fairness (Gini, shut-out rate), speed advantage, welfare, vigilance and server load."""
import numpy as np

from simulator import DAYS, N

MANUAL_MIN_PER_ATTEMPT = 5      # minutes of attention per manual booking attempt
BOT_REQS, HUMAN_REQS = 40, 3    # requests hitting the server per attempt


def gini(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def compute_metrics(res, mech):
    wants, wins, is_bot = res["wants"], res["wins"], res["is_bot"]
    elig = wants >= 10                                   # people who actively wanted slots
    wr = np.divide(wins, wants, out=np.zeros(N), where=wants > 0)
    speed_rank = res["arr_sum"].argsort().argsort()      # 0 = fastest on average
    q = N // 5
    fast, slow = speed_rank < q, speed_rank >= N - q

    def rate(m):
        return wins[m].sum() / max(wants[m].sum(), 1)

    manual = ~is_bot if mech == "fcfs" else np.zeros(N, bool)
    months = DAYS / 30
    return dict(
        served=wins.sum() / wants.sum(),                       # share of demand met
        gini=gini(wr[elig]),                                   # inequality of win-rate
        shutout=float(np.mean(wins[elig] == 0)),               # never won in the period
        fast_rate=rate(fast),                                  # win rate, fastest fifth
        slow_rate=rate(slow),                                  # win rate, slowest fifth
        welfare=res["util_sum"] / max(wins.sum(), 1),          # avg utility of slots won
        vigil_min=wants[manual].sum() * MANUAL_MIN_PER_ATTEMPT / N / months,
        bot_rate=rate(is_bot) if is_bot.any() else np.nan,
        human_rate=rate(~is_bot) if (~is_bot).any() else np.nan,
        reqs_per_day=(wants[is_bot].sum() * BOT_REQS + wants[~is_bot].sum() * HUMAN_REQS) / DAYS,
    )
