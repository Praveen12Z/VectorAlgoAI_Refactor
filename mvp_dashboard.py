# mvp_dashboard.py
# VectorAlgoAI – Strategy Crash-Test MVP Dashboard
# (Public MVP mode: website handles signup; saving/accounts disabled for now)

import traceback
from typing import Dict, Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.strategy_optimizer import optimize_strategy
from components.optimizer_panel import render_optimizer_panel
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
from core.market_fit_analyzer import analyze_market_fit
from components.market_fit_panel import render_market_fit_panel
from components.research_panel import render_research_panel
from components.doctor_panel import render_doctor_panel
from components.root_cause_panel import render_root_cause_panel
from components.gradecard_panel import render_gradecard_panel
# NOTE: These are reserved for future "accounts + saving" versions.
# Keep imports commented to avoid deployment errors if modules are missing.
# from core.report import build_report  # reserved for future use
# from core.strategy_store import (
#     load_user_strategies,
#     save_user_strategy,
#     delete_user_strategy,
# )


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
            "This strategy is *barely* on the right side of zero, but it wouldn’t impress a serious PM yet. "
            "The edge is fragile and could vanish with a small regime shift."
        )
    elif 0.9 <= pf < 1.05:
        verdict = (
            "This wouldn’t survive a single allocation meeting. The edge is not just weak — it’s **non-existent**. "
            "PF around 1 is the market’s way of telling you it’s taking your money for sport."
        )
    else:
        verdict = (
            "This is not a drawdown, this is **structural failure**. "
            "The system is handing over PnL to the market on a consistent basis."
        )

    issues = []
    if pf < 1.0:
        issues.append("Strategy **loses money** (PF < 1). The market is charging you to participate.")
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
        "Tighten stops relative to volatility (e.g. reduce ATR multiples) so losers get cut faster.",
        "Stretch take-profit levels slightly — stop asking the market for crumbs.",
        "Introduce a **regime filter** (trend vs chop, low vs high volatility) and *refuse to trade* in the wrong regime.",
        "Add additional confluence at entry instead of firing signals at every EMA touch.",
    ]
    if avg_rr is not None and avg_rr <= 0:
        actions.append("Rebuild the RR structure: your average winner must be **meaningfully larger** than your average loser.")

    actions_md = "\n\n".join([f"• {txt}" for txt in actions])

    return f"""
💀 **Ruthless Quant PM Review**

{snapshot}

The current configuration would **not** get capital at a professional desk. {verdict}

### Key Issues Detected
{issues_md}

### Non-Negotiable Next Steps
{actions_md}

**Final verdict:** Right now this is closer to a *donor account* than a trading strategy.  
Fix the structure, rebuild the risk/reward, and only then think about deploying real capital.
"""


def run_mvp_dashboard():
    # IMPORTANT: st.set_page_config() should live in app.py (entrypoint)
    st.title("🧪 VectorAlgoAI – Strategy Crash-Test Lab (MVP)")
    st.caption("Early Access MVP • Research Score · Strategy Doctor · Root Cause · Institutional Gradecard")

    with st.sidebar:
        st.header("⚙️ Backtest Settings")
        years = st.slider("Years of history", 1, 15, 2)
        show_trade_lines = st.checkbox("Show trade path lines (last 10 closed trades)", value=False)
        show_rr_labels = st.checkbox("Show RR labels (last 10 closed trades)", value=False)
        st.info("Tip: Edit the strategy YAML, choose history length, then click Run Crash-Test.")

    if "strategy_yaml" not in st.session_state:
        st.session_state["strategy_yaml"] = DEFAULT_STRATEGY_YAML
    if "current_strategy_name" not in st.session_state:
        st.session_state["current_strategy_name"] = ""
    if "bt_result" not in st.session_state:
        st.session_state["bt_result"] = None

    user_strategies = []  # saving disabled in public MVP

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📜 Strategy Logic (YAML - Advanced Mode)")

        saved_names = ["(none)"] + [s.get("name", "") for s in user_strategies]
        selected_name = st.selectbox("Saved strategies", options=saved_names, index=0)

        load_col, delete_col = st.columns(2)

        with load_col:
            if st.button("⬇️ Load Selected", use_container_width=True):
                if selected_name != "(none)":
                    match = next((s for s in user_strategies if s.get("name") == selected_name), None)
                    if match is not None:
                        st.session_state["strategy_yaml"] = match.get("yaml", "")
                        st.session_state["current_strategy_name"] = match.get("name", "")
                        st.success(f"Loaded strategy '{selected_name}'.")
                        st.rerun()
                    else:
                        st.warning("Selected strategy not found.")
                else:
                    st.info("Select a saved strategy first.")

        with delete_col:
            # FIXED: remove invalid else block that caused IndentationError
            st.info("Saving is disabled in this MVP. Full accounts + saved strategies arrive at launch.")

        st.text_input(
            "Strategy name (for exports)",
            key="current_strategy_name",
            placeholder="e.g. NAS100 Pullback v5",
        )

        st.text_area("", height=400, key="strategy_yaml")

        if st.button("💾 Save / Update Strategy", use_container_width=True):
            st.info("Saving is disabled in this MVP. Export your YAML locally for now.")

    with col2:
        run_clicked = st.button("🔴 Run Crash-Test", use_container_width=True)

        if run_clicked:
            try:
                cfg: StrategyConfig = parse_strategy_yaml(st.session_state["strategy_yaml"])
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
        st.info("Run a Crash-Test to see charts and analytics.")
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
    render_optimizer_panel(
         optimizer
    )
    market_fit = analyze_market_fit(
       cfg,
       years
    )

    render_research_panel(cfg, data_start, data_end, data_bars, research, verdict, risk, metrics)
    render_doctor_panel(doctor)
    render_root_cause_panel(root_cause)
    render_gradecard_panel(gradecard)

    st.markdown("---")
    st.subheader("📈 Strategy Evidence")
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
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            increasing_fillcolor="rgba(38,166,154,0.65)",
            decreasing_fillcolor="rgba(239,83,80,0.65)",
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
                                     marker_color="rgba(34,197,94,0.9)", name="Long Entry (Win)"))
        if not loss_long.empty:
            fig.add_trace(go.Scatter(x=loss_long["entry_time"], y=loss_long["entry_price"], mode="markers",
                                     marker_symbol="triangle-up", marker_size=entry_size,
                                     marker_color="rgba(248,113,113,0.95)", name="Long Entry (Loss)"))
        if not win_short.empty:
            fig.add_trace(go.Scatter(x=win_short["entry_time"], y=win_short["entry_price"], mode="markers",
                                     marker_symbol="triangle-down", marker_size=entry_size,
                                     marker_color="rgba(34,197,94,0.9)", name="Short Entry (Win)"))
        if not loss_short.empty:
            fig.add_trace(go.Scatter(x=loss_short["entry_time"], y=loss_short["entry_price"], mode="markers",
                                     marker_symbol="triangle-down", marker_size=entry_size,
                                     marker_color="rgba(248,113,113,0.95)", name="Short Entry (Loss)"))

        if not wins.empty:
            fig.add_trace(go.Scatter(x=wins["exit_time"], y=wins["exit_price"], mode="markers",
                                     marker_symbol="x", marker_size=exit_size,
                                     marker_color="rgba(34,197,94,0.9)", name="Exit (Win)"))
        if not losses.empty:
            fig.add_trace(go.Scatter(x=losses["exit_time"], y=losses["exit_price"], mode="markers",
                                     marker_symbol="x", marker_size=exit_size,
                                     marker_color="rgba(248,113,113,0.95)", name="Exit (Loss)"))

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
                    line=dict(color="rgba(34,197,94,0.7)", width=1.5),
                    name="Winning Trade" if not added_win_legend else "",
                    showlegend=not added_win_legend,
                ))
                added_win_legend = True

            for _, row in losses_for_lines.iterrows():
                fig.add_trace(go.Scatter(
                    x=[row["entry_time"], row["exit_time"]],
                    y=[row["entry_price"], row["exit_price"]],
                    mode="lines",
                    line=dict(color="rgba(248,113,113,0.75)", width=1.5),
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
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displaylogo": False})

    st.subheader("📊 Performance Analytics")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Return", f"{metrics.get('total_return_pct', 0.0):.2f} %")
    m2.metric("Profit Factor", f"{metrics.get('profit_factor', 0.0):.2f}")
    m3.metric("Win Rate", f"{metrics.get('win_rate_pct', 0.0):.2f} %")
    m4.metric("Max Drawdown", f"{metrics.get('max_drawdown_pct', 0.0):.2f} %")
    m5.metric("Number of Trades", int(metrics.get("num_trades", 0)))

    st.subheader("📉 Equity Curve")
    if trades_df.empty or ("pnl" not in trades_df.columns):
        st.info("No equity curve available (no closed trades).")
    else:
        st.line_chart(trades_df["pnl"].cumsum())

    st.subheader("🔬 Trade Evidence")
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

    st.subheader("🔍 Strategy Weaknesses")
    if not weaknesses:
        st.write("- No major weaknesses detected (on this sample).")
    else:
        for w in weaknesses:
            st.write(f"- {w}")

    st.subheader("🧠 Suggestions for Improvement")
    if not suggestions:
        st.write("- No specific suggestions (try different parameters).")
    else:
        for s in suggestions:
            st.write(f"- {s}")

    st.subheader("💡 AI Commentary – Strategy Insights")
    st.markdown(build_ruthless_ai_commentary(metrics, trades_df))


if __name__ == "__main__":
    run_mvp_dashboard()
