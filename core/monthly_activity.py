"""Observed monthly activity, including zero-trade and missing-data months."""
import pandas as pd


def monthly_activity(index, trades):
    if len(index) == 0:
        return []
    local = index.tz_localize(None) if index.tz is not None else index
    months = local.to_period('M')
    entries, exits = {}, {}
    if not trades.empty:
        for row in trades.to_dict('records'):
            entry, exit = pd.Timestamp(row['entry_time']), pd.Timestamp(row['exit_time'])
            if index.tz is not None:
                entry, exit = entry.tz_convert(index.tz), exit.tz_convert(index.tz)
            entry_key, exit_key = entry.strftime('%Y-%m'), exit.strftime('%Y-%m')
            entries[entry_key] = entries.get(entry_key, 0) + 1
            exits.setdefault(exit_key, []).append(float(row['pnl']))
    rows = []
    for month in pd.period_range(months.min(), months.max(), freq='M'):
        key = str(month)
        bars = int((months == month).sum())
        count = entries.get(key, 0)
        boundary = month in (months.min(), months.max())
        coverage = 'No bars' if not bars else 'Boundary month — may be partial' if boundary else 'Interior month — gaps not audited'
        status = 'Not assessed' if boundary or not bars else 'Below 50' if count < 50 else '50–60' if count <= 60 else 'Above 60'
        pnl = exits.get(key, [])
        rows.append({'month': key, 'bars': bars, 'coverage': coverage,
                     'entries': count, 'closed_trades': len(pnl),
                     'net_realized_pnl': sum(pnl), 'frequency_target': status})
    return rows
