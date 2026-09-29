#!/usr/bin/env python3
"""Headline claims, checked on a small run. Run: python tests/test_simulation.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from experiments import run


def test_fair_allocator_removes_speed_advantage():
    fcfs, fair = run("fcfs", 1.0, seeds=3), run("fair", 1.0, seeds=3)
    assert fcfs["fast_rate"] - fcfs["slow_rate"] > 0.5      # arms race: speed decides
    assert abs(fair["fast_rate"] - fair["slow_rate"]) < 0.1  # allocator: speed is irrelevant
    assert fair["gini"] < fcfs["gini"] and fair["shutout"] <= fcfs["shutout"]


def test_bots_gain_nothing_under_allocator():
    r = run("fair", 0.3, seeds=3)
    assert abs(r["bot_rate"] - r["human_rate"]) < 0.05


if __name__ == "__main__":
    for t in (test_fair_allocator_removes_speed_advantage, test_bots_gain_nothing_under_allocator):
        t()
        print("ok  ", t.__name__)
