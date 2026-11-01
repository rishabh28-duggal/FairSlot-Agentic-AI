# FairSlot — Student concept validation (n=20)

## Study scope
Twenty IIT Hyderabad students described their reactions to the FairSlot concept. Inputs were supplied as anonymized student roles/year, direct quotes, and one problem/request per student. This is **qualitative concept feedback**; it is **not** a live deployment, controlled usability experiment, measured adoption study, or demonstration that improvements were implemented.

## Findings

| Theme | Respondent IDs | Observed feedback | Proposed product response |
| --- | --- | --- | --- |
| Trust, fairness and explainability | 1, 2, 6, 7, 12, 15, 16, 19, 20 | Users asked about winning probability, draw bias, fairness credits, frequent versus occasional players, identity abuse, group fairness, history and policy ownership | Publish allocation policy and audit trail; explain credits and outcomes; specify identity controls and governance |
| Preference precision and allocation fit | 3, 5, 8, 14 | Users requested court/time selection, ranked preferences, better time matching and instant booking of uncontested slots | Add ranked slot preferences and exact court/time selection; evaluate uncontested-slot fast path |
| Group booking and changes | 4, 9, 11, 18 | Students described coordination friction, group confirmations, capacity, cancellations and waitlists | Add group confirmation reminders, group-size validation and cancellation/reallocation flows |
| Booking UX and notifications | 10, 13, 17 | Users want to verify parsed requests, avoid repeatedly checking results, and minimize onboarding | Editable parsed preferences, automatic result notifications, streamlined entry |

These are overlapping categories of concerns, not mutually exclusive user segments or quantitative prevalence estimates.

## Selected anonymized verbatim observations
- **R01 — regular tennis player:** "I like that I don't have to open the app the second bookings start." Asked to see probability of winning.
- **R02 — badminton player:** "This solves a problem, but how do I know the draw isn't biased?" Asked for lottery transparency.
- **R04 — group organizer:** "Getting four people to agree on one time is the biggest headache." Asked for confirmation reminders.
- **R06 — badminton player:** "If I lose three times, I'd expect a better chance next time." Asked for fairness-credit explanation.
- **R10 — casual tennis player:** "Typing a request is convenient, but I want to verify what it understood." Asked for editable parsed preferences.
- **R12 — frequent player:** "What stops someone from creating five accounts?" Asked for identity verification.
- **R17 — beginner:** "I would use this only if it's easier than the current booking process." Asked for minimal onboarding.
- **R20 — skeptical user:** "I understand FCFS. Why should I trust a lottery more?" Asked for a clear FCFS comparison.

## Prioritization proposals (not implemented)
1. **Explainability and trust:** expose how the weighted draw works, what credits mean, and why an allocation happened; conduct comprehension tests.
2. **Editable preference confirmation:** show parsed day/time/budget/venue choices before submission and allow edits.
3. **Group coordination and cancellations:** add confirmations, reminders and safe reallocation.
4. **Preference specificity:** support ranked slots or exact court/time preferences.
5. **Anti-abuse and governance:** define identity checks and an auditable policy owner before a real pilot.

## Recommended follow-up measurement
- Ask participants to complete defined tasks, then record completion, errors, time and preference-correction rate.
- Predefine a fairness-comprehension question and measure correct responses before/after the explanation UI.
- Record the number of participants preferring FairSlot to FCFS rather than inferring preference from individual comments.
- A pilot would need consent, venue approval and privacy safeguards.

## Limitations
- The notes do not specify the interview protocol, recruitment method, dates, or whether participants interacted with an actual executable interface.
- The quotes are concept responses and do not establish usage, improvement in success rate, or adoption.
- Algorithmic simulation results in the main README are independent of these 20 participants.
