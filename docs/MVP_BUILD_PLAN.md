# VectorAlgoAI MVP build plan

## Product promise

VectorAlgoAI converts a discretionary or rule-based trading thesis into transparent, testable research and gives an evidence-based capital-readiness verdict. It is not a signal provider or an indicator dashboard.

## Build lanes

| Lane | Outcome | Current priority |
| --- | --- | --- |
| 1. Research contract | One canonical strategy schema and no contradictory execution paths | In progress |
| 2. S/R + price action V2 | Confirmed zones, price-action events, auditable entry reasons and no look-ahead bias | Next |
| 3. Backtest truthfulness | Correct order timing, SL/TP handling, position sizing, trade log and metrics | After V2 events |
| 4. Evidence & diagnosis | Baseline, hold-out, regime breakdown, weaknesses and next experiments | After backtest validation |
| 5. MVP workspace | Thesis, Blueprint, Evidence, Diagnosis and Capital Readiness screens | Built around proven outputs |
| 6. Commercial shell | Website-message consistency, waitlist/early access and deployment workflow | Parallel, after a stable product demo |

## First vertical slice: Support/Resistance + Price Action V2

The first vertical slice must run end-to-end:

1. strategy text / editable blueprint;
2. component parameters;
3. confirmed support or resistance zone events;
4. price-action confirmation and entry reason;
5. next-bar execution and trade record;
6. trade inspection and evidence metrics.

## Non-negotiable engineering rules

- A bar may only use information available when that bar closes.
- A zone must retain its source pivots, price bounds, timeframe and invalidation state.
- Every trade must retain the exact entry conditions and values that created it.
- Backtest, charts, trade inspector and verdict must consume the same canonical output.
- A historical result is evidence, not permission to deploy capital.

## Definition of done for this slice

- Deterministic tests cover pivot confirmation, zone creation, touch/rejection, break/retest and invalidation.
- Tests prove that signals do not depend on future candles.
- A fixture produces inspectable long and short examples.
- The pipeline reports a human-readable reason for every accepted and rejected setup.
