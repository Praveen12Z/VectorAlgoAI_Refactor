"""Sourced research specifications, never fabricated backtest records.

Source concepts are paraphrased. All numeric adaptations are VectorAlgoAI
research choices, not performance claims or faithful replications.
"""
from copy import deepcopy

REVIEWED_ON = "2026-09-16"
COMMON_PROTOCOL = (
    "Long-only v1; no pyramiding; one position at a time. Initial research equity "
    "25,000 account-currency units; planned stop risk 0.5% of current equity. "
    "Gaps and costs can exceed planned risk. Configure the exact instrument, point value, "
    "currency conversion, lot size, spread, commission, slippage and overnight financing "
    "before interpreting returns. NAS100 is a market label, not a broker contract. "
    "Use completed bars and past-only indicators. For specification-only templates, enter "
    "at the next bar open; skip if entry is at/below the stop or at/above a fixed target. "
    "Stops are fixed from the signal; targets use actual entry unless stated otherwise. "
    "Resolve an ambiguous stop/target bar stop-first; fill adverse stop gaps at the worse "
    "available price. ATR14 uses Wilder smoothing; require indicator warm-up. "
    "No automatic news filter unless explicitly specified. Freeze rules and costs before "
    "testing; retain every experiment, use genuinely unseen data, and stress execution costs. "
    "Thirty trades is only a screening floor, not statistical proof. No strategy here is validated."
)

def _item(id, name, family, market, timeframe, source, concept, rules, refinements, gaps, failure, prompt=None):
    return dict(id=id, version="1.0", name=name, family=family, market=market,
        timeframe=timeframe, source_url=source, source_concept=concept,
        reviewed_on=REVIEWED_ON, rules=rules, refinements=refinements,
        implementation_gaps=gaps, failure_modes=failure, prompt=prompt,
        status="SUPPORTED BASELINE — UNVALIDATED" if prompt else "SPECIFICATION ONLY — IMPLEMENTATION REQUIRED")

CATALOG = [
    _item("VA-001", "EMA reclaim with momentum confirmation", "Trend continuation", "NAS100", "1h",
        "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/moving-average-trading-strategies/how-to-trade-price-to-moving-average-crossovers",
        "Price crossing a moving average can define a trend-following trigger.",
        ["EMA20 > EMA50; prior close <= prior EMA20 and current close > current EMA20; RSI14 > 50.",
         "Fixed stop 1.5 ATR14 below entry; target 2 times initial stop distance. Existing positions are liquidated at the sample boundary by the baseline engine; inspect time_exit rows separately.",
         "Entry uses the next available bar open with signal-bar ATR distances anchored to entry. Engine indicator conventions apply; sizing is fractional and does not enforce broker lot or margin limits."],
        "Added explicit EMA alignment, reclaim, RSI threshold and fixed protective exits. Parameters are starting hypotheses, not optimized settings.",
        [], "Whipsaws; overnight gaps; changing costs and broker execution differences.",
        "Trade NAS100 long on 1h when EMA20 is above EMA50. Enter when price closes back above EMA20 and RSI14 above 50. Use ATR14 with a 1.5 ATR stop, target 2R, risk 0.5%, account 25000."),
    _item("VA-002", "20-bar channel breakout", "Price breakout", "NAS100", "1h",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/price-channels",
        "Price channels use rolling highs and lows to identify breaks out of a range.",
        ["At close t, close[t] > maximum high of bars t-20 through t-1; close[t-1] <= that same level.",
         "Stop = signal close minus 2 ATR14; target 3R. No trailing exit or pyramiding."],
        "Excluded the signal bar from the channel and specified entry, stop and target; this is not the complete Turtle system.",
        ["Past-only channel trigger", "Next-open entry"], "False breaks and prolonged sideways markets."),
    _item("VA-003", "RSI2 pullback in a long-term uptrend", "Mean reversion", "NAS100", "1d",
        "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2",
        "Connors-style RSI2 research combines a long-term trend filter with short-term oversold conditions.",
        ["Close > SMA200 and RSI2 < 10 at the completed daily close.",
         "Stop = signal close minus 2 ATR14. Exit next open after a close > SMA5, or after 10 completed holding bars, whichever occurs first; protective stop remains active."],
        "Added a protective stop and ten-bar time exit. These materially change the published concept and require fresh validation.",
        ["SMA trend and price trigger", "Indicator/time exits", "Next-open entry"], "Buying into a persistent decline; overnight gap risk."),
    _item("VA-004", "Bollinger squeeze breakout", "Volatility expansion", "NAS100", "1h",
        "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze",
        "A narrowing Bollinger envelope can precede expansion; the break determines direction.",
        ["Bands = SMA20 +/- 2 population standard deviations of close. Width = (upper-lower)/SMA20.",
         "Previous bar width <= the 20th percentile of the 120 widths ending on that bar. Current close > upper band and previous close <= previous upper band.",
         "Stop = signal close minus 1.5 ATR14; target 2R."],
        "Defined a past-only percentile squeeze threshold and a close-confirmed long breakout.",
        ["Bollinger calculation and squeeze state", "Next-open entry"], "Expansion may reverse; percentile and lookback sensitivity."),
    _item("VA-005", "New York opening-range breakout", "Session breakout", "NAS100", "5m",
        "https://fxopen.com/blog/en/opening-range-breakout-strategy/",
        "Opening-range strategies trade a break of the early session high or low.",
        ["Use America/New_York time and exchange calendar. Freeze high/low of 09:30-09:45; exclude later bars.",
         "First completed 5m close above range high after 09:45 and before 11:00 triggers entry. One attempt per day.",
         "Stop = range low minus one instrument tick; target 2R; flatten at first tradable quote at/after 15:55. Skip incomplete opening ranges."],
        "Fixed session boundaries, trade limit, stop and closing time; DST is handled by the named timezone.",
        ["5m data and session calendar", "Range state and daily trade limit", "Timed exit and next-open entry"], "Opening noise; wide spreads; news-driven reversals."),
    _item("VA-006", "Resistance break and first retest", "Support / resistance", "NAS100", "1h",
        "https://fxopen.com/blog/en/how-can-you-use-a-break-and-retest-strategy-in-trading/",
        "A breakout followed by a retest can turn former resistance into a candidate support level.",
        ["A pivot high exceeds the two highs on each side and becomes usable only after the two right-hand bars close. Use the most recent confirmed pivot, at most 50 bars old.",
         "After a close above that pivot, freeze its level and ATR14. Within the next 10 bars, first low within +/-0.25 frozen ATR of the level and close above it triggers entry. Cancel on close below level-0.25 ATR.",
         "Stop = retest-bar low minus 0.25 frozen ATR; target 2R. Retire level after one attempt."],
        "Specified pivot confirmation delay, tolerance, expiry and invalidation to avoid hindsight-drawn levels.",
        ["Confirmed pivot state", "Break/retest lifecycle", "Structural stop and next-open entry"], "Unstable levels; parameter sensitivity; delayed pivot recognition."),
    _item("VA-007", "Previous-day low sweep and reclaim", "False breakout", "NAS100", "15m",
        "https://academy.ftmo.com/lesson/how-to-spot-breakouts-and-fakeouts/",
        "A failed break returns inside a previously established price boundary.",
        ["Freeze the previous complete 09:30-16:00 America/New_York session low; use the exchange calendar.",
         "Between 09:45 and 14:00, a bar low below that level and close above it triggers a long. One attempt per day.",
         "Stop = signal low minus one tick; target 2R; flatten at first quote at/after 15:55."],
        "Uses an observable prior-day level and same-bar reclaim. Price action does not prove institutional intent or a liquidity hunt.",
        ["Prior-session levels and calendar", "Sweep trigger", "Structural stop, timed exit and next-open entry"], "Strong downtrends can overwhelm a reclaim."),
    _item("VA-008", "Fresh demand-zone first retest", "Supply / demand", "XAUUSD", "1h",
        "https://academy.ftmo.com/lesson/supply-and-demand-trading/",
        "Demand-zone research looks for revisits to a consolidation preceding an upward departure.",
        ["Base = three completed bars with combined high-low <= ATR14 at base end. Next bar must close above base high by >=1.5 frozen ATR; only then create the zone [base low, base high].",
         "Use newest zone only. First later bar touching zone within 20 bars must close above zone high to signal; otherwise retire the touched zone. Invalidate on close below zone low.",
         "Stop = zone low minus 0.25 frozen ATR; target 2R. One attempt per zone."],
        "Made base size, departure strength, freshness and invalidation measurable; long demand variant only, supply-side shorts are not included.",
        ["Zone construction and lifecycle", "Structural stop and next-open entry"], "Zones can reflect noise; no evidence that a zone contains unfilled institutional orders."),
    _item("VA-009", "Session VWAP pullback continuation", "Volume / price action", "NQ futures", "5m",
        "https://academy.ftmo.com/lesson/vwap-technical-indicator/",
        "VWAP pullback setups combine session price location with a return toward the volume-weighted mean.",
        ["Compute cumulative sum(((high+low+close)/3)*volume)/sum(volume), reset at 09:30 America/New_York, using exchange trade volume.",
         "From 10:00 to 14:00: previous close > previous VWAP; current low <= current VWAP and close > it; current VWAP > VWAP three bars earlier.",
         "Stop = signal low minus one tick; target 2R; one attempt per day; flatten at first quote at/after 15:55."],
        "Fixed session anchor, volume provenance, slope and reclaim. Do not substitute index or unlabelled CFD tick volume.",
        ["Futures contract and volume feed", "Session VWAP", "Trade limits, timed exit and next-open entry"], "Volume-feed differences; contract rolls; choppy sessions."),
    _item("VA-010", "NFP surprise with gold price confirmation", "Fundamental + technical", "XAUUSD", "5m",
        "https://www.oanda.com/us-en/skills-and-insights/education/fundamental-analysis/macroeconomics/what-is-non-farm-payroll/",
        "The payroll release provides economic information and can produce sharp market volatility. The source does not establish this strategy's profitability.",
        ["Use archived release timestamp T, first-published payroll actual and consensus snapshot recorded before T. Trade only if actual-consensus <= -50000 jobs; never use later revisions.",
         "Freeze high of the 30 minutes before T. From T+15 to T+60 minutes, first completed 5m close above that high triggers a long; one attempt per release.",
         "Stop = signal low minus one tick; target 2R; flatten at first quote at/after T+120 minutes. Skip missing/stale consensus or incomplete bars."],
        "Original VectorAlgoAI hypothesis inspired by the economic event: a weak payroll surprise plus observed gold strength. No fixed macro direction is guaranteed.",
        ["Point-in-time actual/consensus archive", "Release-aligned bars and event state", "Event cost profile, timed exit and next-open entry"], "Wages and revisions may dominate headline payrolls; extreme spreads and slippage."),
]


def catalog_origin(source_text):
    for item in CATALOG:
        if item['prompt'] and source_text.strip() == item['prompt']:
            return {key: item[key] for key in ('id', 'version', 'name', 'source_url', 'reviewed_on')}
    return None


def load_template(state, item):
    if item['implementation_gaps'] or not item['prompt']:
        raise ValueError("This specification is not executable by the current engine.")
    for key in ('bt_result', 'blueprint_yaml', 'blueprint_schema', 'strategy_yaml',
                'approved_strategy_yaml', 'evidence_yaml_editor', 'blueprint_assumptions_accepted'):
        state.pop(key, None)
    state.update(ai_text=item['prompt'], ai_market=item['market'], ai_timeframe=item['timeframe'],
        blueprint_approved=False, active_workspace_stage='thesis',
        current_strategy_name=item['name'], experiment_version=item['version'],
        experiment_hypothesis=item['refinements'], experiment_parent=None)


def catalog_export(item):
    return {**deepcopy(item), 'research_protocol': COMMON_PROTOCOL, 'validation_status': 'NOT TESTED'}
