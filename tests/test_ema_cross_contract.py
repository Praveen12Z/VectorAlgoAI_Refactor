import yaml
from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.research_contract import strategy_contract_issues


def test_explicit_ema_crossover_is_approved_entry_capability():
    text = "Buy when EMA 20 crosses above EMA 50 and RSI 14 is above 50. Enter long on the next candle. Use a stop-loss of 2 ATR and a take-profit of 3 ATR."
    schema = build_strategy_from_text(text)
    assert any(c["component"] == "ema_cross_entry" for c in schema["components"])
    strategy = yaml.safe_load(compile_schema_to_yaml(schema, market="NAS100", timeframe="1h"))
    assert any(c.get("type") == "cross_above" and c["left"] == "ema20" and c["right"] == "ema50" for c in strategy["entry"]["long"])
    assert any(c["type"] == "atr_sl" and c["multiple"] == 2 for c in strategy["exit"]["long"])
    assert not strategy_contract_issues(strategy)


def test_ema_alignment_alone_does_not_invent_entry_trigger():
    schema = build_strategy_from_text("EMA 20 above EMA 50 and RSI 14 above 50 with stop loss 2 ATR")
    strategy = yaml.safe_load(compile_schema_to_yaml(schema, market="NAS100", timeframe="1h"))
    assert any("entry trigger" in issue for issue in strategy_contract_issues(strategy))
