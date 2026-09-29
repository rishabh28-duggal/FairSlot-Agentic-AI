#!/usr/bin/env python3
"""End-to-end demo: a residential community's tennis courts, 8 residents + 1 friend group, 3 booking windows.
Run:  python demo.py            (offline rule-based parsing)
      GROQ_API_KEY=... python demo.py        (LLM parsing + LLM-written group message)
"""
import random

from agents import MODEL, PersonalAgent, llm_available
from allocator import FairAllocator, Slot
from group_agent import GroupAgent

SLOTS = [
    Slot("TUE-1800", "Court 1 - Tue 18:00-20:00", "tennis", "tue", 18, 2, 600),
    Slot("TUE-2000", "Court 1 - Tue 20:00-22:00", "tennis", "tue", 20, 2, 500),
    Slot("SAT-0700", "Court 1 - Sat 07:00-09:00", "tennis", "sat", 7, 2, 500),
    Slot("SAT-1700", "Court 1 - Sat 17:00-19:00", "tennis", "sat", 17, 2, 700),
]
LABEL = {s.id: s.label for s in SLOTS}

RESIDENTS = {
    "Aarav":   "Tennis, weekday evenings, 2 hrs, under ₹700",
    "Meera":   "I'd love a Saturday morning tennis session, around 7am, 2 hours",
    "Karthik": "tennis any weekday after 6pm, max ₹550, 2 hours",
    "Neha":    "Tennis on Saturday evening please, 2 hours, ₹800 budget",
    "Rohan":   "tennis on the weekend, flexible on time, 2 hrs",
    "Ishita":  "Tennis Tuesday or Saturday, evenings, 2 hours",
    "Vikram":  "Tennis whenever, I'm flexible, 2 hrs",
    "Sana":    "Tennis Tue or Thu evening, max ₹500 please, 2 hrs",
}
GROUP_MESSAGES = {
    "Arjun": "Tennis weekends, mornings or evenings, 2 hrs",
    "Divya": "Saturday works, evening only, 2 hours",
    "Kabir": "Sat or Sun, after 4pm, 2 hrs",
    "Tara":  "Can only do Saturday morning, before 10am, 2 hrs",
}
GROUP_REPLIES = {"Arjun": "yes", "Divya": "yes, works for me", "Kabir": "I'm in", "Tara": "can't make it, sorry"}


def main():
    mode = f"LLM ON ({MODEL})" if llm_available() else "OFF (offline rule-based parser)"
    print(f"LLM parsing: {mode}\n")

    print("1) PERSONAL AGENTS: free text -> validated structured preferences")
    agents = {}
    for name, text in RESIDENTS.items():
        a = PersonalAgent(name)
        p = a.hear(text)
        agents[name] = a
        print(f'  {name:8s} "{text}"\n           -> {p.summary()}')

    print("\n2) GROUP AGENT: organiser problem")
    g = GroupAgent("Arjun", GROUP_MESSAGES)
    for s, who, mean_u in g.availability(SLOTS):
        print(f"  {s.label}: {len(who)}/{len(g.agents)} available {who}")
    short = g.shortlist(SLOTS)
    print(f"  Quorum needed: {g.quorum} of {len(g.agents)}")
    print(f"  Proposal to group chat: {g.proposal_text(short)}")
    print(f"  Replies: {GROUP_REPLIES}")
    confirmed = g.collect(GROUP_REPLIES)
    group_interest = g.declare(SLOTS, confirmed)
    print(f"  Confirmed: {confirmed} -> " + ("quorum met, group declares interest" if group_interest
                                             else "no quorum, group does NOT enter the draw"))

    print("\n3) FAIR ALLOCATOR: 3 booking windows (fairness credits carry over)")
    alloc = FairAllocator(seed=7)
    rng = random.Random(1)
    for w in range(1, 4):
        interests = [a.declare(SLOTS) for a in agents.values()] + ([group_interest] if group_interest else [])
        rng.shuffle(interests)   # submission order is irrelevant: nobody wins by being first
        awards = alloc.close_window(interests, SLOTS)
        print(f"\n  Window {w}: {len(SLOTS)} slots, {len(interests)} requests")
        for rid, a in sorted(awards.items(), key=lambda kv: kv[1].rank):
            got = LABEL[a.slot_id] if a.slot_id else "-"
            print(f"    #{a.rank} {rid:14s} weight {a.weight:4.2f} -> {got}")
        if w == 1:
            print("\n  Explanations (window 1):")
            for rid, a in sorted(awards.items()):
                print(f"    {rid}: {a.explanation}")
    print("\nNote how anyone who missed out has a higher odds weight in the next window.")


if __name__ == "__main__":
    main()
