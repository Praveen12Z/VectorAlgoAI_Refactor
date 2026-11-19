"""Saved experiment review and comparison."""
import difflib
import json
import pandas as pd
import streamlit as st
from core.experiment_tracking import DECISIONS, annotate, comparison, metadata


def label(record):
    meta = metadata(record)
    return f"{record['strategy_name']} · {meta.get('version') or 'Unversioned'} · {meta.get('kind', 'run')} · {record['record_hash'][:10]}"


def render_saved_evidence(record, key):
    st.subheader("Backtest results")
    st.caption(
        f"{record['market']} · {record['timeframe']} · {record['validation_status']} · "
        f"{record.get('data_bars', 'Unknown')} bars"
    )
    if record.get("data_start") and record.get("data_end"):
        st.write(f"{record['data_start']} through {record['data_end']}")

    rows = []
    for label_text, field in (
        ("Full sample", "full_metrics"),
        ("Development", "development_metrics"),
        ("Holdout", "holdout_metrics"),
    ):
        metrics = record.get(field)
        if metrics:
            rows.append({
                "Sample": label_text,
                "Trades": metrics.get("num_trades"),
                "Net return (%)": metrics.get("total_return_pct"),
                "Win rate (%)": metrics.get("win_rate_pct"),
                "Profit factor": metrics.get("profit_factor"),
                "Max drawdown (%)": metrics.get("max_drawdown_pct"),
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    with st.expander("Backtest rules and execution assumptions"):
        st.code(record.get("strategy_yaml") or "Rules unavailable.", language="yaml")
        st.json(record.get("execution_assumptions") or {})
        coverage = (record.get("full_metrics") or {}).get("data_coverage")
        if coverage:
            st.json(coverage)

    st.subheader("Full-sample trade ledger")
    trades = record.get("trade_records")
    if trades:
        ledger = pd.DataFrame(trades)
        st.dataframe(ledger, hide_index=True, use_container_width=True)
        st.download_button("Download trades CSV", ledger.to_csv(index=False),
                           "trades.csv", "text/csv", key=f"{key}_trades")
    elif trades == [] and (record.get("full_metrics") or {}).get("num_trades") == 0:
        st.info("The backtest closed zero trades.")
    else:
        st.info("This saved record has no available trade ledger.")
    st.download_button(
        "Download evidence JSON", json.dumps(record, indent=2, ensure_ascii=False, default=str),
        f"{record['record_hash'][:12]}_evidence.json", "application/json", key=f"{key}_json",
    )


def render_uploaded_evidence():
    st.caption("Open downloaded evidence JSON files to review or compare them without database access.")
    files = st.file_uploader("Evidence JSON files", type=["json"], accept_multiple_files=True)
    records = {}
    required = {"record_hash", "strategy_name", "market", "timeframe", "validation_status"}
    for file in files:
        try:
            record = json.loads(file.getvalue())
            if not isinstance(record, dict) or any(
                not isinstance(record.get(field), str) or not record[field] for field in required
            ):
                raise ValueError("Missing required evidence fields")
            for field in ("execution_assumptions", "full_metrics", "development_metrics", "holdout_metrics"):
                if not isinstance(record.get(field), dict):
                    raise ValueError(f"Invalid {field}")
            if not isinstance(record.get("trade_records"), list):
                raise ValueError("Invalid trade ledger")
            records[record["record_hash"]] = record
        except (ValueError, UnicodeError):
            st.warning(f"Could not open {file.name} as a VectorAlgoAI evidence record.")
    if records:
        render_experiment_library(list(records.values()), records.__getitem__, persist=None)


def render_experiment_library(records, load_record, persist):
    by_hash = {r['record_hash']: r for r in records}
    if persist is not None:
        st.caption("Latest 25 records, including review revisions.")
    with st.expander("Run history"):
        st.dataframe(pd.DataFrame([{
            "Name": r['strategy_name'], "Version": metadata(r).get('version', ''),
            "Kind": metadata(r).get('kind', 'run'), "Decision": metadata(r).get('decision', 'Not reviewed'),
            "Validation": r['validation_status'], "Saved": r.get('created_at'),
        } for r in records]), hide_index=True, use_container_width=True)
    selected = st.selectbox("Review saved record", list(by_hash), format_func=lambda h: label(by_hash[h]))
    record = load_record(selected)
    results_tab, review_tab, comparison_tab = st.tabs(["Results", "Review decision", "Compare runs"])
    with results_tab:
        render_saved_evidence(record, key="saved_experiment")
    with review_tab:
        _render_review(record, selected, persist)
    with comparison_tab:
        _render_comparison(record, selected, by_hash)


def _render_review(record, selected, persist):
    meta = metadata(record)
    st.caption(f"Parent version: {meta.get('parent_record_hash') or 'None'}")
    with st.form(f"review_{selected}"):
        name = st.text_input("Research name", value=record['strategy_name'])
        version = st.text_input("Version label", value=meta.get('version', ''))
        hypothesis = st.text_area("Hypothesis / reason for change", value=meta.get('hypothesis', ''))
        decision = st.selectbox("Research decision", DECISIONS, index=DECISIONS.index(meta.get('decision')) if meta.get('decision') in DECISIONS else 0)
        notes = st.text_area("Review notes", value=meta.get('notes', ''))
        submitted = st.form_submit_button("Save review revision" if persist else "Prepare review download")
    if submitted:
        if not name.strip() or not version.strip():
            st.error("Enter a research name and version label.")
        else:
            original = dict(record)
            original['strategy_name'] = name.strip()
            revision = annotate(original, version=version, hypothesis=hypothesis,
                parent_record_hash=meta.get('parent_record_hash'), decision=decision, notes=notes, review=True)
            if persist is None:
                st.session_state[f"uploaded_review_{selected}"] = revision
            else:
                result = persist(revision)
                if result.get("saved"):
                    st.success("Review saved. Original evidence preserved.")
                else:
                    st.error(result.get("message", "Could not save review."))
    if persist is None and (revision := st.session_state.get(f"uploaded_review_{selected}")):
        st.download_button("Download review JSON", json.dumps(revision, indent=2),
                           f"{revision['record_hash'][:12]}_review.json", "application/json")


def _render_comparison(record, selected, by_hash):
    if len(by_hash) < 2:
        st.info("Add another backtest to compare runs.")
        return
    st.subheader("Compare saved records")
    other = st.selectbox("Compare with", [h for h in by_hash if h != selected], format_func=lambda h: label(by_hash[h]))
    rows = comparison(record, by_hash[other])
    changed = [r['Field'] for r in rows[:11] if r['A'] != r['B']]
    st.info("Changed: " + (", ".join(changed) if changed else "No differences in the compared configuration fields."))
    st.caption("Descriptive comparison only. Shared dates do not prove identical data. Previously viewed hold-out data is not untouched; differences do not establish causation.")
    st.dataframe(pd.DataFrame([{k: str(v) if v is not None else 'Not recorded' for k, v in row.items()} for row in rows]), hide_index=True, use_container_width=True)
    with st.expander("Exact rule changes (A → B)"):
        st.code(''.join(difflib.unified_diff((record.get('strategy_yaml') or '').splitlines(True),
            (by_hash[other].get('strategy_yaml') or '').splitlines(True), fromfile='A', tofile='B')) or 'No YAML changes.', language='diff')
