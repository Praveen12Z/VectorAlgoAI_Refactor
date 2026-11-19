# Published research implementation: first delivery

Reviewed 19 November 2026. This release does not claim published returns have been reproduced.

## Library
PR-001 is a monthly, multi-asset time-series momentum replication target. Its original instruments and portfolio conventions need to be verified before execution. It cannot be launched through the EMA/ATR parser. Source: https://www.aqr.com/insights/research/journal-article/time-series-momentum

PR-002 adds the US-stock opening-activity selection component from the research linked in its library entry. Its source population is equities. Applying it to futures, currencies or gold would be a distinct hypothesis. Our older VA-005 template remains separately identified; it is not the published study.

## Running the selector
In Sourced strategy starters, choose PR-002. Supply two CSVs with columns:
`session,symbol,open,high,low,close,volume`.

The daily file contains regular-session OHLCV. The opening file contains exactly one completed 09:30–09:35 America/New_York bar per stock/session. Dates use YYYY-MM-DD; prices are USD and volume is shares. Do not upload arbitrary five-minute bars, futures, index proxies or broker trade reports.

Include at least 15 prior daily sessions (for true-range calculation) and 14 prior opening sessions per stock. The supplied session union defines the expected historical sessions. This is not an exchange-calendar verification. A date missing from all inputs cannot be detected. The UI requires confirmation of opening timing; date-only files cannot prove it.

Select Screen research candidates. The audit includes every supplied opening row, with historical-data exclusions and filter/ranking outcomes. Warm-up rows are retained with reasons, not treated as executed trades. Export both the CSV audit and hashed JSON record; keep input files to rerun. Database persistence is not connected for this new record type.

## Declared implementation choices
- Arithmetic mean true range, not a silent substitution of Wilder smoothing.
- Dojis excluded before ranking; alphabetical ties.
- Current/future daily OHLCV is excluded from each session's features.
- Historical availability is checked per symbol against supplied sessions.
- Source universe completeness, delisted securities, split treatment and short availability are not verified.
- No trade executions, account equity, expected profit or deployment verdict are produced.
- Initial UI upload limits keep this a bounded research sample, not a full-universe production scanner.

## Next execution gates
Obtain a survivorship-safe universe and exchange calendar, verify bar timestamps and corporate actions, reconcile the original smoothing/selection conventions, then implement stop-order entry, conservative intrabar fills, borrow constraints, source portfolio sizing and end-of-session liquidation. Only after those steps can we compare a full backtest with the publication. All source changes and independent adaptations must be versioned.

## Verification
Tests cover past-only features, long/short/doji handling, price filters, deterministic top-20 ties, missing histories, zero opening volume, duplicate rejection and evidence input identity. Synthetic fixtures check correctness; they are not market-performance evidence.
