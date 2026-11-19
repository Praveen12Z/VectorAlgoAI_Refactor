# VectorAlgoAI: focused paid launch by 19 February 2027

Owner: Praveen Kumar. Start: 19 November 2026. Target: 19 February 2027.
Status: delivery plan, not a guarantee of completion, customer acquisition or profit.

## Decision
The full product vision remains: describe -> precise approved rules -> realistic testing -> explain weaknesses -> preserve evidence -> demo automation.
The first commercial release serves Nasdaq intraday traders testing explicit strategies. MNQ is the first execution/data profile. Indicators and price action both belong in the product. General news interpretation, ML prediction, unrestricted natural-language strategy support and five production EAs remain later work, not three-month promises.

Core promise: show whether the system tested the trader's intended rules, why each trade occurred, what the evidence supports, and what remains unknown. Never promise profitability or a minimum trade count.

## Critical assessment
- We have repeatedly tuned indicator examples and report labels before proving a complete research workflow.
- Rule correctness, representative data and execution realism matter more than a research grade.
- Sparse trades may be valid; unexplained sparse trades are a product failure.
- A broad campaign before pilot retention is measured risks amplifying distrust and support demand.
- A calendar date cannot override correctness, isolation or payment-access failures.

## Weekly delivery and acceptance gates
| Period | Deliverable | Acceptance evidence |
|---|---|---|
| Nov 19-25 | Signal diagnostics and data-source/timeframe honesty | Counts reconcile with entries; unsupported timeframes fail explicitly; first pilot interviews arranged by founder |
| Nov 26-Dec 2 | NinjaTrader minute import and MNQ execution profile | Timezone and bar timestamp convention confirmed; file fingerprint; gap/duplicate checks; integer contracts, tick rounding and explicit costs tested |
| Dec 3-9 | Five-minute research workflow | Aggregated candles manually checked against exported source; completed higher-timeframe bars only; selected-session boundaries and DST tested |
| Dec 10-16 | One price-action strategy contract | Define zones, swings, base, confirmation, expiry, both directions and exits with founder; ambiguous rules block execution; do not silently approximate discretionary rules |
| Dec 17-23 | Chart-level trade and rejection inspection | At least 20 selected trade/rejection examples reconciled with frozen rules; zero unexplained critical mismatches; zero-trade cases included |
| Dec 24-30 | Save, reopen and reproduce | Same rules, dataset hash, engine version and costs reproduce trades; immutable versions; separate users cannot read each other's records |
| Dec 31-Jan 6 | Frozen validation and report | Development and unseen evaluation identified; net costs/stress assumptions shown; all variants tracked; sample limitations explicit |
| Jan 7-13 | Private pilot with 5 traders | Observe each trader complete their own supported research task; record errors, task time and requests; revise onboarding from observations |
| Jan 14-20 | Paid pilot offer | Publish exact capability/limitation list and tested sample report; interview willingness to pay; payment and cancellation journeys verified |
| Jan 21-27 | Reliability and retention | At least 4 of 5 pilot users complete core task without developer intervention; measure repeat usage; resolve critical defects |
| Jan 28-Feb 3 | Optional demo adapter OR core hardening | Only if research gates passed: one platform/strategy adapter with logged signal parity; otherwise spend week on core reliability; never live orders by default |
| Feb 4-10 | Launch rehearsal | Fresh-user login -> payment -> import -> research -> save -> reopen -> export; support, restore, rollback and privacy/access checks |
| Feb 11-19 | Staged public launch | Start with 20-30-user cohort; monitor failures and support; widen promotion only if release and business gates below hold |

## Release gates
- No unresolved critical data, rule, execution, account-isolation or payment-access defects.
- Dataset identity, actual coverage, instrument, timezone, costs and engine version visible in evidence.
- Repeated frozen runs reproduce trades; unsupported features block clearly.
- Trade/blocked-signal counts reconcile; checks include no-trade and losing strategies.
- Users can save, reopen and export; restore and rollback procedures exercised.
- Claims describe research capability, never guaranteed returns or statistical certainty from a fixed trade threshold.
- Demo automation is not advertised as shipped unless its own parity and safety gates pass.

## Business gates and founder work
These are proposed operating targets, not predictions: 10 interviews by week 4; 5 active pilot traders; 10 paying customers as the first commercial milestone. Pilot completion target >=80%; target >=50% of activated pilot users returning to run another research task within 14 days. Report actual numerators and denominators. Small cohorts are directional, not proof of product-market fit.

Founder: recruit and interview traders, supply 10 chart examples with exact intent, confirm the export timezone and desired first strategy, observe pilot sessions, price the offer and own customer support. Do not solicit anyone's credentials or broker keys.
Development: data import/profile, contracts, execution, diagnostics, evidence persistence, tests and deployment. No background work or automatic future delivery is implied; progress occurs during working sessions.

At four hours/day, allocate roughly 2.5 hours to implementation/testing, 1 hour to trader/customer work and 0.5 hour to review and defect prioritization. If fewer days are available, reduce scope before reducing verification.

## Promotion
Founder can prepare educational demonstrations through the existing LinkedIn, X, Instagram and Discord presence. No external messages, campaigns or spend are authorized by this document. Use real traceable examples, including a rejected or losing strategy. Avoid claims of a profitable library until each strategy has supporting evidence. Postpone paid acquisition until users can activate, repeat the workflow and retain without excessive manual support.

## Day-one delivery
Added cumulative and independent rule pass counts, qualifying-bar counts, open-position/equity blockers, executed entries and final-bar signals lacking a next open. Saved metrics carry these diagnostics. Dashboard exposes them under "Why this many trades?". Unsupported data-source timeframes now fail before cache lookup rather than falling back to hourly bars. This does not yet add MNQ import or five-minute support.
