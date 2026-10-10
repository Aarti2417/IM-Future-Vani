# IndiaMART Historical Call Log Dispositions & Outcomes

## Overview
Analysis of disposition distributions from historical VANI bot call attempts:

| Disposition Reason | Count |
|---|---|
| Unknown | 769 |
| 386.0 | 102 |
| 380.0 | 88 |
| 385.0 | 27 |
| 383.0 | 8 |
| 11.0 | 4 |
| 382.0 | 2 |

## Key Protocol:
Calls tagged with 'do_not_call' or 'frustrated_dnc' must instantly trigger `end_interaction` with an apology without further sales attempts.
