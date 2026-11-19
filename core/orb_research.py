"""Opening-volume stock selection, not an execution backtest or profitability claim."""
from hashlib import sha256
import json
import numpy as np
import pandas as pd

SOURCE = 'https://concretumgroup.com/wp-content/uploads/2026/02/A-Profitable-Day-Trading-Strategy-For-The-U.S.-Equity-Market.pdf'
VERSION = 'orb-stock-selection-1'


def _frame(data):
    required = ['session', 'symbol', 'open', 'high', 'low', 'close', 'volume']
    missing = set(required) - set(data.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    f = data[required].copy()
    f['session'] = pd.to_datetime(f['session'], format='%Y-%m-%d', errors='raise')
    if f['session'].isna().any() or (f['session'] != f['session'].dt.normalize()).any():
        raise ValueError('Use nonempty session dates in YYYY-MM-DD format.')
    if f['symbol'].isna().any():
        raise ValueError('Symbols cannot be empty.')
    f['symbol'] = f['symbol'].astype(str).str.strip().str.upper()
    if f['symbol'].eq('').any() or f.duplicated(['session','symbol']).any():
        raise ValueError('Require a nonempty symbol and one row per symbol/session.')
    columns = ['open','high','low','close','volume']
    f[columns] = f[columns].apply(pd.to_numeric, errors='raise')
    if not np.isfinite(f[columns].to_numpy()).all():
        raise ValueError('OHLCV must be finite.')
    if (f[['open','high','low','close']] <= 0).any().any() or (f.volume < 0).any():
        raise ValueError('Prices must be positive and volume nonnegative.')
    if ((f.high < f[['open','close','low']].max(axis=1)) |
            (f.low > f[['open','close','high']].min(axis=1))).any():
        raise ValueError('Invalid OHLC range.')
    return f.sort_values(['session','symbol']).reset_index(drop=True)


def screen_opening_range(daily, opening):
    """At 09:35 NY, rank supplied US stocks using only earlier sessions.

    `opening` contains completed 09:30-09:35 NY bars, not arbitrary 5m bars.
    Daily history and opening history must cover the same exchange sessions.
    Date-only input cannot verify timestamps, exchange holidays or universe completeness.
    ATR is arithmetic mean true range: a declared implementation convention.
    """
    daily, opening = _frame(daily), _frame(opening)
    sessions = sorted(set(daily.session) | set(opening.session))
    lookbacks = {date: sessions[max(0, i - 15):i] for i, date in enumerate(sessions)}
    dg = {s: g.set_index('session') for s,g in daily.groupby('symbol')}
    og = {s: g.set_index('session') for s,g in opening.groupby('symbol')}
    rows = []
    for bar in opening.itertuples(index=False):
        date, symbol = bar.session, bar.symbol
        past = lookbacks[date]
        row = dict(session=date.strftime('%Y-%m-%d'), symbol=symbol,
                   direction='long' if bar.close > bar.open else 'short' if bar.close < bar.open else 'none',
                   opening_high=float(bar.high), opening_low=float(bar.low),
                   relative_volume=None, prior_atr14=None, planned_stop_distance=None,
                   rank=None, selected=False, reason='')
        d = dg.get(symbol)
        o = og[symbol]
        if len(past) < 15 or d is None or not set(past).issubset(d.index) or not set(past[-14:]).issubset(o.index):
            row['reason'] = 'Incomplete prior daily/opening history'
            rows.append(row)
            continue
        history = d.loc[past]
        prev_close = history.close.shift(1)
        tr = pd.concat([history.high-history.low, (history.high-prev_close).abs(),
                        (history.low-prev_close).abs()], axis=1).max(axis=1)
        atr = float(tr.iloc[-14:].mean())
        avg_volume = float(history.volume.iloc[-14:].mean())
        avg_open_volume = float(o.loc[past[-14:], 'volume'].mean())
        rv = float(bar.volume / avg_open_volume) if avg_open_volume > 0 else None
        row.update(relative_volume=rv, prior_atr14=atr, planned_stop_distance=atr*0.1)
        reasons = []
        if bar.open <= 5: reasons.append('Opening price must exceed $5')
        if avg_volume < 1_000_000: reasons.append('Prior average daily volume below 1,000,000')
        if atr <= .5: reasons.append('Prior ATR must exceed $0.50')
        if rv is None or rv < 1: reasons.append('Opening relative volume below 1 or unavailable')
        if row['direction'] == 'none': reasons.append('Opening doji: no direction')
        row['reason'] = '; '.join(reasons) if reasons else 'Eligible before top-20 selection'
        rows.append(row)
    result = pd.DataFrame(rows, columns=['session','symbol','direction','opening_high','opening_low',
        'relative_volume','prior_atr14','planned_stop_distance','rank','selected','reason'])
    for _, group in result[result.reason == 'Eligible before top-20 selection'].groupby('session'):
        ordered = group.sort_values(['relative_volume','symbol'], ascending=[False,True])
        for rank, idx in enumerate(ordered.index, 1):
            result.loc[idx, ['rank','selected','reason']] = [rank, rank <= 20,
                'Selected candidate — not an executed trade' if rank <= 20 else 'Outside top 20']
    return result


def selection_record(daily_bytes, opening_bytes, results):
    record = dict(engine_version=VERSION, source_url=SOURCE,
        status='STOCK SELECTION ONLY — NO BACKTEST',
        assumptions={'opening_bar':'09:30–09:35 America/New_York, completed',
            'atr':'14-session arithmetic mean true range', 'tie_break':'symbol ascending',
            'universe':'user supplied; completeness and survivorship bias unverified',
            'execution':'not simulated', 'profitability':'not assessed'},
        daily_sha256=sha256(daily_bytes).hexdigest(), opening_sha256=sha256(opening_bytes).hexdigest(),
        candidates=json.loads(results.to_json(orient='records')))
    record['record_hash'] = sha256(json.dumps(record,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return record
