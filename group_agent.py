
 
"""
Group agent: solves the organiser problem.
Parses each member's availability, finds slots most of the group can do, proposes them,
collects yes/no replies, and enters the draw only once a quorum confirms.
The LLM (optional) only words the group-chat message; slot scoring and quorum are plain code.
"""
from __future__ import annotations
 
import json
import math
import re
 
import agents
from agents import PersonalAgent, slot_utility
from allocator import Interest
 
_YES = re.compile(r"\b(yes|yep|yeah|yup|sure|works|in|confirm(?:ed)?|ok|okay|done|count me in)\b|👍")
_NO = re.compile(r"\b(no|nope|can't|cant|cannot|not|busy|out|sorry)\b")
 
 
def is_yes(reply: str) -> bool:
    r = reply.lower()
    return bool(_YES.search(r)) and not _NO.search(r)
 
 
class GroupAgent:
    """Solves the organiser problem: find a slot most of the group can do, get quorum, then declare."""
 
    def __init__(self, organiser: str, messages: dict, activity="tennis", quorum_frac=0.6):
        self.organiser, self.activity = organiser, activity
        self.agents = {}
        for name, text in messages.items():
            a = PersonalAgent(name)
            p = a.hear(text)
            p.activity = p.activity or activity
            self.agents[name] = a
        self.quorum = math.ceil(quorum_frac * len(self.agents))
 
    def availability(self, slots):
        rows = []
        for s in slots:
            ok = [(n, u) for n, a in self.agents.items() if (u := slot_utility(a.prefs, s)) > 0]
            rows.append((s, [n for n, _ in ok], sum(u for _, u in ok) / len(ok) if ok else 0.0))
        return rows
 
    def shortlist(self, slots, k=2):
        rows = [r for r in self.availability(slots) if len(r[1]) >= self.quorum]
        rows.sort(key=lambda r: (-len(r[1]), -r[2]))
        return rows[:k]
 
    def proposal_text(self, shortlist) -> str:
        n = len(self.agents)
        if not shortlist:   # nothing reached quorum: never let the LLM invent slots
            return (f"No slot works for {self.quorum} of {n} people yet, so I am not proposing one. "
                    "If your timing has any give, tell me and I will re-check.")
        facts = [{"slot": s.label, "price_rs": s.price, "available": f"{len(who)} of {n}"} for s, who, _ in shortlist]
        fallback = ("Hi all! Court options: " + "; ".join(
            f"{f['slot']} (Rs{f['price_rs']}, works for {f['available']})" for f in facts)
            + f". Reply yes/no. I'll enter us in the booking draw once {self.quorum} of {n} confirm.")
        if facts and agents.llm_available():
            try:
                txt = agents.call_llm("Write a friendly group-chat message (max 45 words) proposing these slots and asking "
                               "for yes/no. Use ONLY the facts given; copy each slot label exactly as written. No emojis.", json.dumps(facts), 150).strip()
                if all(f["slot"] in txt for f in facts):   # guardrail: must state every slot exactly
                    return txt
            except Exception as e:
                agents.debug(f"LLM message failed, using template: {type(e).__name__}: {e}")
        return fallback
 
    def collect(self, replies: dict) -> list:
        return [n for n in self.agents if n in replies and is_yes(replies[n])]
 
    def declare(self, slots, confirmed):
        if len(confirmed) < self.quorum:
            return None
        utils = {}
        for s in slots:
            us = [u for n in confirmed if (u := slot_utility(self.agents[n].prefs, s)) > 0]
            if len(us) >= self.quorum:
                utils[s.id] = round(len(us) / len(confirmed) * sum(us) / len(us), 4)
        return Interest(f"group:{self.organiser}", utils, members=list(confirmed)) if utils else None
 
 
