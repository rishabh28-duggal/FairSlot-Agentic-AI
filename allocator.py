"""
Deterministic fair allocator: declared-interest window -> weighted lottery -> fairness credits.

No LLM in here. Agents translate language into `Interest` objects; this module alone decides
who gets scarce inventory. Properties:
  * Speed-blind: submission order and arrival time are never inputs.
  * Draw priority depends only on fairness credits (losers gain odds, recent winners lose odds).
  * Each requester then takes their highest-utility slot still free (serial dictatorship), so
    declaring true preferences is the best strategy: reports never change the draw order.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

ALPHA, STREAK_CAP, BETA, DECAY = 0.6, 8, 1.5, 0.9


def fairness_weights(streak, recent_wins, alpha=ALPHA, cap=STREAK_CAP, beta=BETA):
    """Odds weight: grows with consecutive losses, shrinks with recent wins."""
    streak = np.asarray(streak, float)
    recent_wins = np.asarray(recent_wins, float)
    return (1 + alpha * np.minimum(streak, cap)) / (1 + beta * recent_wins)


def draw_order(rng, weights):
    """Weighted random order (Efraimidis-Spirakis). Returns indices, first = drawn first."""
    w = np.asarray(weights, float)
    keys = rng.random(len(w)) ** (1 / w)
    return np.argsort(-keys)


@dataclass(frozen=True)
class Slot:
    id: str
    label: str
    activity: str
    day: str            # mon..sun
    start_hour: float
    duration_hours: float
    price: int


@dataclass
class Interest:
    requester_id: str
    utilities: dict                      # slot_id -> utility in (0, 1]
    members: list = field(default_factory=list)   # people this request covers (groups)

    def __post_init__(self):
        if not self.members:
            self.members = [self.requester_id]


@dataclass
class Award:
    requester_id: str
    slot_id: str | None
    rank: int            # position in the draw (0 = had no acceptable slot)
    n: int               # number of requests drawn
    weight: float        # odds weight used this window
    weight_next: float   # odds weight for the next window
    explanation: str


class FairAllocator:
    def __init__(self, seed: int = 0):
        self.seed = seed
        self.window = 0
        self.streak = defaultdict(int)
        self.recent = defaultdict(float)

    def member_weight(self, uid: str) -> float:
        return float(fairness_weights([self.streak[uid]], [self.recent[uid]])[0])

    def request_weight(self, interest: Interest) -> float:
        # A group's odds are the average of its members', so forming a group never beats going solo.
        return float(np.mean([self.member_weight(m) for m in interest.members]))

    def close_window(self, interests, slots):
        self.window += 1
        rng = np.random.default_rng([self.seed, self.window])
        slot_index = {s.id: k for k, s in enumerate(slots)}
        labels = {s.id: s.label for s in slots}

        def usable(i):
            return {s: u for s, u in i.utilities.items() if s in slot_index and u > 0}

        # sorted by id: the order requests were submitted in is irrelevant by construction
        ordered = sorted(interests, key=lambda i: i.requester_id)
        reqs = [i for i in ordered if usable(i)]
        skipped = [i for i in ordered if not usable(i)]
        weights = np.array([self.request_weight(i) for i in reqs])
        order = draw_order(rng, weights) if len(reqs) else []

        free = set(slot_index)
        raw = {}
        for rank, k in enumerate(order, start=1):
            i = reqs[k]
            cand = {s: u for s, u in usable(i).items() if s in free}
            sid = max(cand, key=lambda s: (cand[s], -slot_index[s])) if cand else None
            if sid:
                free.remove(sid)
            raw[i.requester_id] = (sid, rank, float(weights[k]), i)

        # update fairness credits
        participants = set()
        for sid, _, _, i in raw.values():
            for m in i.members:
                participants.add(m)
                if sid:
                    self.streak[m] = 0
                    self.recent[m] = self.recent[m] * DECAY + 1
                else:
                    self.streak[m] += 1
                    self.recent[m] *= DECAY
        for uid in list(self.recent):
            if uid not in participants:
                self.recent[uid] *= DECAY

        awards = {}
        n = len(reqs)
        for rid, (sid, rank, w, i) in raw.items():
            wn = self.request_weight(i)
            if sid:
                text = f"Drawn {rank} of {n} (odds weight {w:.2f}). You got {labels[sid]}."
            else:
                text = (f"Drawn {rank} of {n} (odds weight {w:.2f}), but every slot you could take "
                        f"was already gone. Your odds weight next window: {wn:.2f}.")
            awards[rid] = Award(rid, sid, rank, n, w, wn, text)
        for i in skipped:
            awards[i.requester_id] = Award(i.requester_id, None, 0, n, 0.0, self.request_weight(i),
                                           "No slot in this window matched your constraints.")
        return awards
