# mvp_dashboard.py
# VectorAlgoAI – Strategy Crash-Test MVP Dashboard
# (Public MVP mode: website handles signup; saving/accounts disabled for now)
import traceback
from typing import Dict, Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data_loader import load_ohlcv
from core.indicators import apply_all_indicators
from core.strategy_config import parse_strategy_yaml, StrategyConfig
from core.backtester_adapter import run_backtest_v2
from core.research_score import calculate_research_score
from core.capital_verdict import get_capital_verdict
from core.risk_report import build_risk_report
from core.strategy_doctor import build_strategy_doctor
from core.root_cause_analyzer import analyze_root_cause
from core.gradecard import build_gradecard
from core.strategy_optimizer import optimize_strategy
from core.market_fit_analyzer import analyze_market_fit

from components.research_panel import render_research_panel
from components.doctor_panel import render_doctor_panel
from components.root_cause_panel import render_root_cause_panel
from components.gradecard_panel import render_gradecard_panel
from components.optimizer_panel import render_optimizer_panel
from components.market_fit_panel import render_market_fit_panel
from components.optimizer_panel import render_optimizer_panel
from components.executive_summary_panel import (
    render_executive_summary
)
from core.strategy_mutation_engine import generate_mutations
from core.mutation_evaluator import evaluate_mutations

from components.mutation_panel import (
    render_mutation_panel
)
from core.evolution_lab import run_evolution_lab

from components.evolution_lab_panel import (
    render_evolution_lab
)

from core.strategy_mutation_engine import generate_mutations
from core.mutation_evaluator import evaluate_mutations
from components.mutation_panel import render_mutation_panel
from components.ai_strategy_builder_panel import render_ai_strategy_builder_panel
from components.workspace_ui import (
    inject_workspace_styles,
    render_workspace_header,
    render_workspace_sidebar,
)





DEFAULT_STRATEGY_YAML = """\
name: "NAS100 Momentum v5 – Pullback System"
market: "NAS100"
timeframe: "1h"

indicators:
  - name: ema20
    type: ema
    period: 20
    source: close

  - name: ema50
    type: ema
    period: 50
    source: close

  - name: ema200
    type: ema
    period: 200
    source: close

  - name: rsi14
    type: rsi
    period: 14
    source: close

  - name: atr14
    type: atr
    period: 14

entry:
  long:
    - left: ema20
      op: ">"
      right: ema50

    - left: ema50
      op: ">"
      right: ema200

    - left: close
      op: "<"
      right: ema20

    - left: close
      op: ">"
      right: ema50

    - left: rsi14
      op: "<"
      right: 55

    - left: rsi14
      op: ">"
      right: 40

  short:
    - left: ema20
      op: "<"
      right: ema50

    - left: ema50
      op: "<"
      right: ema200

    - left: close
      op: ">"
      right: ema20

    - left: close
      op: "<"
      right: ema50

    - left: rsi14
      op: ">"
      right: 45

    - left: rsi14
      op: "<"
      right: 60

exit:
  long:
    - type: atr_sl
      atr_col: atr14
      multiple: 2.0

    - type: atr_tp
      atr_col: atr14
      multiple: 3.5

  short:
    - type: atr_sl
      atr_col: atr14
      multiple: 2.0

    - type: atr_tp
      atr_col: atr14
      multiple: 3.5

risk:
  capital: 10000
  risk_per_trade_pct: 1.0
"""


def _render_evidence_intro(bt: Dict[str, Any] | None) -> None:
    """Keep the evidence screen calm: state first, detailed proof second."""
    if bt is None:
        title = "No evidence generated yet"
        copy = "Your approved research contract is ready. Select the historical window in the sidebar, then run the test."
    elif bt.get("error"):
        title = "Evidence test needs attention"
        copy = "The test did not complete. Review the message below, adjust the research contract if needed, then run it again."
    elif bt.get("contract_issues"):
        title = "Research contract needs completion"
        copy = "Complete the missing executable rules in the Blueprint before generating historical evidence."
    else:
        data_range = bt.get("data_range")
        if data_range and len(data_range) == 3:
            start, end, bars = data_range
            title = "Historical evidence generated"
            copy = f"{start} to {end} · {bars:,} bars analysed. This is historical evidence, not a performance forecast."
        else:
            # Cached results from earlier app versions may not include the
            # display-only range metadata. They must never crash the Evidence page.
            title = "Evidence ready to review"
            copy = "Historical results are available. Run the test again to refresh the research record with the selected data window."
    st.markdown(
        f'<div class="va-evidence-banner"><div class="va-evidence-kicker">Research record</div>'
        f'<div class="va-evidence-title">{title}</div><div class="va-evidence-meta">{copy}</div></div>',
        unsafe_allow_html=True,
    )


def _render_workspace_landing(view: str) -> None:
    """Focused product pages for the permanent workspace navigation."""
    if view == "home":
        has_blueprint = bool(st.session_state.get("blueprint_schema"))
        has_evidence = bool(st.session_state.get("bt_result"))
        stage = "Evidence review" if has_evidence else ("Blueprint review" if has_blueprint else "Strategy brief")
        evidence_count = "1 record" if has_evidence else "0 records"
        capital_state = "Under review" if has_evidence else "Not assessed"
        st.markdown(
            '<section class="va-dashboard-hero">'
            '<div><div class="va-dashboard-eyebrow">Vector AlgoAI Research OS</div>'
            '<h1>Turn a trading thesis into a capital decision.</h1>'
            '<p>Build explicit rules, challenge them against historical evidence, diagnose fragility and advance only what survives.</p></div>'
            '<div class="va-dashboard-pill">Research mode · Active</div></section>',
            unsafe_allow_html=True,
        )
        one, two, three = st.columns(3)
        with one:
            st.markdown(f'<div class="va-card va-card-blue"><div class="va-card-title">Active stage</div><div class="va-card-value">{stage}<br><span style="color:#718197;font-size:.76rem">Continue the current research record.</span></div></div>', unsafe_allow_html=True)
        with two:
            st.markdown(f'<div class="va-card va-card-teal"><div class="va-card-title">Evidence vault</div><div class="va-card-value">{evidence_count}<br><span style="color:#718197;font-size:.76rem">Backtests remain tied to approved rules.</span></div></div>', unsafe_allow_html=True)
        with three:
            st.markdown(f'<div class="va-card va-card-amber"><div class="va-card-title">Capital readiness</div><div class="va-card-value">{capital_state}<br><span style="color:#718197;font-size:.76rem">No capital verdict without evidence.</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="va-section-title">Research pipeline</div><div class="va-section-copy">One controlled workflow from idea to deployment readiness.</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="va-dashboard-strip">'
            '<div class="va-pipeline-card"><div class="va-pipeline-step">01 · Define</div><div class="va-pipeline-title">Make the thesis testable</div><div class="va-pipeline-copy">Translate natural language into explicit entry, exit, risk and regime rules.</div></div>'
            '<div class="va-pipeline-card"><div class="va-pipeline-step">02 · Challenge</div><div class="va-pipeline-title">Generate evidence</div><div class="va-pipeline-copy">Backtest after costs, inspect every trade and isolate unstable assumptions.</div></div>'
            '<div class="va-pipeline-card"><div class="va-pipeline-step">03 · Decide</div><div class="va-pipeline-title">Gate capital</div><div class="va-pipeline-copy">Approve, refine or reject the strategy with an explainable verdict.</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        primary, secondary = st.columns([1, 2.4])
        with primary:
            if st.button("＋  New strategy", type="primary", use_container_width=True):
                st.session_state["active_workspace_stage"] = "thesis"
                st.rerun()
        with secondary:
            if has_evidence and st.button("Continue evidence review", use_container_width=True):
                st.session_state["active_workspace_stage"] = "evidence"
                st.rerun()
            elif has_blueprint and st.button("Continue blueprint review", use_container_width=True):
                st.session_state["active_workspace_stage"] = "blueprint"
                st.rerun()
    elif view == "library":
        st.markdown('<div class="va-page-kicker">Strategy library</div><div class="va-title">Research records, not signal lists.</div><div class="va-subtitle">Saved strategies and their evidence will live here. The first record is created when you approve your thesis.</div>', unsafe_allow_html=True)
        st.info("No saved strategy records yet. Start a New strategy to create the first research record.")
    else:
        st.markdown('<div class="va-page-kicker">Settings</div><div class="va-title">Workspace settings</div><div class="va-subtitle">Account and research defaults will be configured here as the MVP grows.</div>', unsafe_allow_html=True)
        st.markdown('<div class="va-card"><div class="va-card-title">Current default</div><div class="va-card-value">NAS100 · 1h research timeframe</div></div>', unsafe_allow_html=True)


def build_ruthless_ai_commentary(metrics: Dict[str, Any], trades_df: pd.DataFrame) -> str:
    grade = metrics.get("grade", "-")
    total_ret = float(metrics.get("total_return_pct", 0.0))
    pf = float(metrics.get("profit_factor", 0.0))
    win_rate = float(metrics.get("win_rate_pct", 0.0))
    num_trades = int(metrics.get("num_trades", 0))

    avg_rr = None
    if isinstance(trades_df, pd.DataFrame) and ("rr" in trades_df.columns):
        rr_series = trades_df["rr"].dropna()
        if not rr_series.empty:
            avg_rr = float(rr_series.mean())

    snapshot = (
        f"**Snapshot:** Grade **{grade}**, Total Return **{total_ret:.2f}%**, "
        f"Profit Factor **{pf:.2f}**, Win Rate **{win_rate:.2f}%**, Trades **{num_trades}**."
    )

    if pf >= 1.05 and total_ret > 0:
        verdict = (
            "The result is positive on this sample, but the edge remains fragile and needs validation across other market conditions."
        )
    elif 0.9 <= pf < 1.05:
        verdict = (
            "The result is close to breakeven. The available evidence does not yet support a claim of a reliable edge."
        )
    else:
        verdict = (
            "The current rule set is losing on this historical sample and requires redesign before further validation."
        )

    issues = []
    if pf < 1.0:
        issues.append("The strategy loses on this sample (PF < 1).")
    elif pf < 1.1:
        issues.append("Profit factor is barely above 1 — any extra friction (slippage, spreads, fees) will erase it.")
    if win_rate < 45:
        issues.append("Win rate is **low (< 45%)**. You are relying heavily on big winners that rarely show up.")
    if num_trades < 20:
        issues.append("Sample size is **small**. Treat conclusions as fragile; this is a preview, not truth.")
    if avg_rr is not None and avg_rr <= 0:
        issues.append(
            f"Average RR is **{avg_rr:.2f}**, meaning you are structured to lose over time — "
            "you risk more on losers than you gain on winners."
        )
    if not issues:
        issues.append("No single catastrophic metric, but nothing here screams *institutional-grade edge* either.")

    issues_md = "\n\n".join([f"• {txt}" for txt in issues])

    actions = [
        "Test stop placement relative to volatility, without changing multiple variables at once.",
        "Test take-profit placement as a controlled experiment, not an assumption.",
        "Introduce a **regime filter** (trend vs chop, low vs high volatility) and *refuse to trade* in the wrong regime.",
        "Add additional confluence at entry instead of firing signals at every EMA touch.",
    ]
    if avg_rr is not None and avg_rr <= 0:
        actions.append("Rebuild the RR structure: your average winner must be **meaningfully larger** than your average loser.")

    actions_md = "\n\n".join([f"• {txt}" for txt in actions])

    return f"""
**Research commentary**

{snapshot}

Capital readiness is based on the evidence available today. {verdict}

### Key Issues Detected
{issues_md}

### Suggested research steps
{actions_md}

**Current conclusion:** Do not increase capital exposure from this test alone. Complete the next validation step before changing the readiness decision.
"""


def run_mvp_dashboard():
    if "active_workspace_stage" not in st.session_state:
        st.session_state["active_workspace_stage"] = "home"
    if "strategy_yaml" not in st.session_state:
        st.session_state["strategy_yaml"] = DEFAULT_STRATEGY_YAML
    if "current_strategy_name" not in st.session_state:
        st.session_state["current_strategy_name"] = ""
    if "bt_result" not in st.session_state:
        st.session_state["bt_result"] = None
    if "active_workspace_view" not in st.session_state:
        st.session_state["active_workspace_view"] = "home"

    inject_workspace_styles()
    years, show_trade_lines, show_rr_labels = render_workspace_sidebar()
    active_stage = st.session_state.get("active_workspace_stage", "home")
    render_workspace_header(active_stage)

    if active_stage in {"home", "library", "settings"}:
        _render_workspace_landing(active_stage)
        return

    if active_stage in {"thesis", "blueprint"}:
        render_ai_strategy_builder_panel(active_stage)
        return

    if active_stage not in {"evidence", "diagnosis", "readiness"}:
        st.session_state["active_workspace_stage"] = "thesis"
        st.rerun()

    run_clicked = False
    if active_stage == "evidence":
        st.markdown('<div class="va-page-kicker">Backtest Results</div><div class="va-title">Test the approved rules against history</div><div class="va-subtitle">Realistic costs included. Historical evidence remains separate from future validation.</div>', unsafe_allow_html=True)
        _render_evidence_intro(st.session_state.get("bt_result"))
        if not st.session_state.get("blueprint_approved"):
            st.info("Approve the Rule Blueprint before running the backtest.")
        run_clicked = st.button(
            "Run Backtest", use_container_width=False, type="primary",
            disabled=not st.session_state.get("blueprint_approved", False),
        )

        approved_yaml = st.session_state.get("approved_strategy_yaml")
        if not isinstance(approved_yaml, str) or not approved_yaml.strip():
            approved_yaml = st.session_state.get("blueprint_yaml")
        if isinstance(approved_yaml, str) and approved_yaml.strip():
            # Initialize the editable Evidence copy once. A separate widget key
            # prevents a stale blank text area from erasing the approved contract.
            if not isinstance(st.session_state.get("evidence_yaml_editor"), str) or not st.session_state.get("evidence_yaml_editor", "").strip():
                st.session_state["evidence_yaml_editor"] = approved_yaml

        with st.expander("Advanced configuration", expanded=False):
            st.caption("Optional. Inspect or adjust the machine-readable rules before running the test.")
            st.text_input("Strategy name (for exports)", key="current_strategy_name", placeholder="e.g. NAS100 Pullback v5")
            st.text_area("YAML strategy configuration", height=330, key="evidence_yaml_editor")

    if run_clicked:
        try:
            evidence_yaml = st.session_state.get("evidence_yaml_editor")
            if not isinstance(evidence_yaml, str) or not evidence_yaml.strip():
                evidence_yaml = st.session_state.get("approved_strategy_yaml") or st.session_state.get("blueprint_yaml")
            cfg: StrategyConfig = parse_strategy_yaml(evidence_yaml)
            st.session_state["strategy_yaml"] = evidence_yaml
            df_price = load_ohlcv(cfg.market, cfg.timeframe, years)

            if df_price is None or df_price.empty:
                st.session_state["bt_result"] = {"error": "No price data loaded."}
            else:
                df_feat = apply_all_indicators(df_price, cfg)
                metrics, weaknesses, suggestions, trades_df = run_backtest_v2(df_feat, cfg)

                st.session_state["bt_result"] = {
                    "cfg": cfg,
                    "df_feat": df_feat,
                    "metrics": metrics,
                    "weaknesses": weaknesses,
                    "suggestions": suggestions,
                    "trades_df": trades_df,
                    "data_range": (df_price.index[0].date(), df_price.index[-1].date(), len(df_price)),
                }

        except Exception as e:
            st.session_state["bt_result"] = {"error": str(e), "traceback": traceback.format_exc()}

    bt = st.session_state.get("bt_result")
    if bt is None:
        st.info("Run an evidence test to unlock this research stage.")
        return

    if "error" in bt:
        st.error("Error running backtest:")
        st.code(bt["error"])
        if "traceback" in bt:
            st.code(bt["traceback"])
        return

    cfg: StrategyConfig = bt["cfg"]
    df_feat: pd.DataFrame = bt["df_feat"]
    metrics = bt["metrics"]
    weaknesses = bt["weaknesses"]
    suggestions = bt["suggestions"]
    trades_df: pd.DataFrame = bt["trades_df"]
    data_start, data_end, data_bars = bt["data_range"]

    # =====================================================
    # RESEARCH LAYER
# =====================================================

    research = calculate_research_score(metrics)
    verdict = get_capital_verdict(metrics)
    risk = build_risk_report(metrics)

    doctor = build_strategy_doctor(metrics)
    root_cause = analyze_root_cause(metrics)

    optimizer = optimize_strategy(metrics)

    gradecard = build_gradecard(metrics)

    if active_stage == "diagnosis":
        st.markdown('<div class="va-page-kicker">Strategy Diagnosis</div><div class="va-title">Why this version failed</div><div class="va-subtitle">VectorAlgoAI separates observed weaknesses from suggested experiments.</div>', unsafe_allow_html=True)
        market_fit = analyze_market_fit(cfg, years)
        render_doctor_panel(doctor)
        render_root_cause_panel(root_cause)
        render_market_fit_panel(market_fit)
        render_optimizer_panel(optimizer)
        return

    if active_stage == "readiness":
        st.markdown('<div class="va-page-kicker">Deployment Readiness</div><div class="va-title">Should this strategy receive capital?</div><div class="va-subtitle">Capital decisions are gated by evidence—not optimism.</div>', unsafe_allow_html=True)
        market_fit = analyze_market_fit(cfg, years)
        render_executive_summary(research, verdict, doctor, gradecard, optimizer, market_fit)
        render_research_panel(cfg, data_start, data_end, data_bars, research, verdict, risk, metrics)
        render_gradecard_panel(gradecard)
        return

    st.markdown('<div class="va-section-title">Baseline evidence</div>', unsafe_allow_html=True)
    st.markdown('<div class="va-section-copy">This is the first historical result for the approved rules. It is evidence to examine—not a capital recommendation.</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total return", f"{metrics.get('total_return_pct', 0.0):.2f} %")
    m2.metric("Profit factor", f"{metrics.get('profit_factor', 0.0):.2f}")
    m3.metric("Win rate", f"{metrics.get('win_rate_pct', 0.0):.2f} %")
    m4.metric("Max drawdown", f"{metrics.get('max_drawdown_pct', 0.0):.2f} %")
    m5.metric("Trades", int(metrics.get("num_trades", 0)))

    st.markdown('<div class="va-section-title">Trade inspection</div>', unsafe_allow_html=True)
    st.markdown('<div class="va-section-copy">Inspect the executed trades against the price series. Enable trade paths or R labels only when you need them.</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df_feat.index,
            open=df_feat["open"],
            high=df_feat["high"],
            low=df_feat["low"],
            close=df_feat["close"],
            name="Price",
            increasing_line_width=2,
            decreasing_line_width=2,
            increasing_line_color="#0f9f9a",
            decreasing_line_color="#d05268",
            increasing_fillcolor="rgba(15,159,154,0.62)",
            decreasing_fillcolor="rgba(208,82,104,0.62)",
        )
    )

    for col, label in [("ema20", "EMA 20"), ("ema50", "EMA 50"), ("ema200", "EMA 200")]:
        if col in df_feat.columns:
            fig.add_trace(go.Scatter(x=df_feat.index, y=df_feat[col], mode="lines", name=label, line=dict(width=1.3)))

    if isinstance(trades_df, pd.DataFrame) and (not trades_df.empty):
        closed = trades_df.dropna(subset=["exit_time"]).copy()
        wins = closed[closed["pnl"] > 0]
        losses = closed[closed["pnl"] <= 0]

        win_long = wins[wins["direction"] == "long"]
        win_short = wins[wins["direction"] == "short"]
        loss_long = losses[losses["direction"] == "long"]
        loss_short = losses[losses["direction"] == "short"]

        entry_size = 9
        exit_size = 8

        if not win_long.empty:
            fig.add_trace(go.Scatter(x=win_long["entry_time"], y=win_long["entry_price"], mode="markers",
                                     marker_symbol="triangle-up", marker_size=entry_size,
                                     marker_color="rgba(15,159,154,0.92)", name="Long Entry (Win)"))
        if not loss_long.empty:
            fig.add_trace(go.Scatter(x=loss_long["entry_time"], y=loss_long["entry_price"], mode="markers",
                                     marker_symbol="triangle-up", marker_size=entry_size,
                                     marker_color="rgba(208,82,104,0.95)", name="Long Entry (Loss)"))
        if not win_short.empty:
            fig.add_trace(go.Scatter(x=win_short["entry_time"], y=win_short["entry_price"], mode="markers",
                                     marker_symbol="triangle-down", marker_size=entry_size,
                                     marker_color="rgba(15,159,154,0.92)", name="Short Entry (Win)"))
        if not loss_short.empty:
            fig.add_trace(go.Scatter(x=loss_short["entry_time"], y=loss_short["entry_price"], mode="markers",
                                     marker_symbol="triangle-down", marker_size=entry_size,
                                     marker_color="rgba(208,82,104,0.95)", name="Short Entry (Loss)"))

        if not wins.empty:
            fig.add_trace(go.Scatter(x=wins["exit_time"], y=wins["exit_price"], mode="markers",
                                     marker_symbol="x", marker_size=exit_size,
                                     marker_color="rgba(15,159,154,0.92)", name="Exit (Win)"))
        if not losses.empty:
            fig.add_trace(go.Scatter(x=losses["exit_time"], y=losses["exit_price"], mode="markers",
                                     marker_symbol="x", marker_size=exit_size,
                                     marker_color="rgba(208,82,104,0.95)", name="Exit (Loss)"))

        if show_trade_lines and not closed.empty:
            closed_for_lines = closed.tail(10)
            wins_for_lines = closed_for_lines[closed_for_lines["pnl"] > 0]
            losses_for_lines = closed_for_lines[closed_for_lines["pnl"] <= 0]

            added_win_legend = False
            added_loss_legend = False

            for _, row in wins_for_lines.iterrows():
                fig.add_trace(go.Scatter(
                    x=[row["entry_time"], row["exit_time"]],
                    y=[row["entry_price"], row["exit_price"]],
                    mode="lines",
                    line=dict(color="rgba(15,159,154,0.72)", width=1.5),
                    name="Winning Trade" if not added_win_legend else "",
                    showlegend=not added_win_legend,
                ))
                added_win_legend = True

            for _, row in losses_for_lines.iterrows():
                fig.add_trace(go.Scatter(
                    x=[row["entry_time"], row["exit_time"]],
                    y=[row["entry_price"], row["exit_price"]],
                    mode="lines",
                    line=dict(color="rgba(208,82,104,0.78)", width=1.5),
                    name="Losing Trade" if not added_loss_legend else "",
                    showlegend=not added_loss_legend,
                ))
                added_loss_legend = True

        if show_rr_labels and ("rr" in closed.columns):
            label_trades = closed.tail(10).copy()
            texts = []
            for rr in label_trades["rr"]:
                if pd.isna(rr):
                    texts.append("")
                else:
                    sign = "+" if rr > 0 else ""
                    texts.append(f"RR {sign}{rr:.1f}")

            fig.add_trace(go.Scatter(
                x=label_trades["exit_time"], y=label_trades["exit_price"],
                mode="text", text=texts, textposition="top center",
                textfont=dict(size=9), name="RR", showlegend=False
            ))

    fig.update_layout(
        dragmode="pan",
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=30, b=0),
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fbfdff",
        font=dict(color="#5c6f86"),
        colorway=["#2563eb", "#0f9f9a", "#7c8ba1"],
        xaxis=dict(gridcolor="#e9eff5", zerolinecolor="#dbe4ee"),
        yaxis=dict(gridcolor="#e9eff5", zerolinecolor="#dbe4ee"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displaylogo": False})

    st.markdown('<div class="va-section-title">Equity path</div>', unsafe_allow_html=True)
    if trades_df.empty or ("pnl" not in trades_df.columns):
        st.info("No equity curve available (no closed trades).")
    else:
        st.line_chart(trades_df["pnl"].cumsum())

    st.markdown('<div class="va-section-title">Trade record</div>', unsafe_allow_html=True)
    if trades_df.empty:
        st.warning("No trades generated by this strategy on the selected data.")
    else:
        st.dataframe(trades_df, use_container_width=True)
        csv_bytes = trades_df.to_csv(index=False).encode("utf-8")

        def _safe_name(txt: str) -> str:
            return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (txt or "").strip()) or "strategy"

        base_name = _safe_name(st.session_state.get("current_strategy_name") or cfg.name)
        market_tag = _safe_name(cfg.market)

        st.download_button("Download Trades CSV", csv_bytes, f"{base_name}_{market_tag}_trades.csv", "text/csv", use_container_width=True)

        current_yaml = st.session_state.get("strategy_yaml", DEFAULT_STRATEGY_YAML)
        st.download_button("Download Strategy YAML", current_yaml.encode("utf-8"), f"{base_name}_{market_tag}.yaml", "text/yaml", use_container_width=True)

    st.markdown('<div class="va-section-title">Observed weaknesses</div>', unsafe_allow_html=True)
    if not weaknesses:
        st.write("- No major weaknesses detected (on this sample).")
    else:
        for w in weaknesses:
            st.write(f"- {w}")

    st.markdown('<div class="va-section-title">Research next steps</div>', unsafe_allow_html=True)
    if not suggestions:
        st.write("- No specific suggestions (try different parameters).")
    else:
        for s in suggestions:
            st.write(f"- {s}")

    with st.expander("Detailed strategy commentary", expanded=False):
        st.markdown(build_ruthless_ai_commentary(metrics, trades_df))


if __name__ == "__main__":
    from components.paid_access import require_paid_access
    if require_paid_access():
        run_mvp_dashboard()
