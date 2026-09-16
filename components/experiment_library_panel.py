"""Saved experiment review and comparison."""
import difflib
import pandas as pd
import streamlit as st
from core.experiment_tracking import DECISIONS, annotate, comparison, metadata


def label(record):
    meta = metadata(record)
    return f"{record['strategy_name']} · {meta.get('version') or 'Unversioned'} · {meta.get('kind', 'run')} · {record['record_hash'][:10]}"


def render_experiment_library(records, load_record, persist):
    by_hash = {r['record_hash']: r for r in records}
    st.caption("Latest 25 records, including review revisions. Reviews preserve the original evidence and do not change validation status.")
    st.dataframe(pd.DataFrame([{
        "Name": r['strategy_name'], "Version": metadata(r).get('version', ''),
        "Kind": metadata(r).get('kind', 'run'), "Decision": metadata(r).get('decision', 'Not reviewed'),
        "Validation": r['validation_status'], "Saved": r.get('created_at'),
    } for r in records]), hide_index=True, use_container_width=True)
    selected = st.selectbox("Review saved record", list(by_hash), format_func=lambda h: label(by_hash[h]))
    record = by_hash[selected]
    meta = metadata(record)
    st.caption(f"Parent version: {meta.get('parent_record_hash') or 'None'}")
    with st.form(f"review_{selected}"):
        name = st.text_input("Research name", value=record['strategy_name'])
        version = st.text_input("Version label", value=meta.get('version', ''))
        hypothesis = st.text_area("Hypothesis / reason for change", value=meta.get('hypothesis', ''))
        decision = st.selectbox("Research decision", DECISIONS, index=DECISIONS.index(meta.get('decision')) if meta.get('decision') in DECISIONS else 0)
        notes = st.text_area("Review notes", value=meta.get('notes', ''))
        submitted = st.form_submit_button("Save review revision")
    if submitted:
        if not name.strip() or not version.strip():
            st.error("Enter a research name and version label.")
        else:
            original = load_record(selected)
            original['strategy_name'] = name.strip()
            revision = annotate(original, version=version, hypothesis=hypothesis,
                parent_record_hash=meta.get('parent_record_hash'), decision=decision, notes=notes, review=True)
            result = persist(revision)
            if result.get('saved'):
                st.success("Review saved. Original evidence preserved.")
            else:
                st.error(result.get('message', 'Could not save review.'))
    if len(records) < 2:
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
