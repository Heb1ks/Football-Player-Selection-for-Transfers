# Browser walkthrough on 15 October 2026

The local app was exercised in the Codex in-app browser, including a narrow initial viewport and a 1440 × 1050 desktop viewport. This is a manual walkthrough, not an exhaustive browser compatibility or accessibility audit.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Initial pool | 27 attack candidates for summer 2023, age at most 30 | screenshots/discovery.jpg |
| Factual profile | Rasmus Højlund: prior, individual RF and context RF scores; dated inputs; observed outcome explicitly separated | screenshots/profile.jpg |
| Save and compare | Højlund and Openda stored and displayed as two cards | screenshots/shortlist.jpg |
| Persistence | After reload, shortlist count remained 2 and Højlund remained visible in My shortlist | Browser walkthrough |
| Filter and context scenario | Age limit set to 25, Arsenal context, extended RF selected | screenshots/scenario.jpg |
| Counterfactual disclosure | Changed-destination profile explicitly states that no observed outcome exists for that scenario | screenshots/scenario.jpg |
| Reset | Restored Recorded destination and Individual RF | Browser walkthrough |
| Board | 11 versioned task cards shown; detailed criteria opened for DIP-02, DIP-06 and DIP-08 | screenshots/board.jpg and task screenshots |

CSV row parity, invalid requests, feature isolation and private-path handling are checked in the automated HTTP/core suite. The browser walkthrough does not establish that scouts find the interface useful; real user validation is pending.
