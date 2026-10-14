import yaml
from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.research_contract import strategy_contract_issues


def test_explicit_three_atr_take_profit_is_not_rewritten_to_two_r():
    text = "Buy when EMA 20 crosses above EMA 50 and RSI 14 is above 50. Enter long on the next candle. Use a stop-loss of 2 ATR and a take-profit of 3 ATR."
    schema = build_strategy_from_text(text)
    assert any(c["component"] == "atr_target" and c["params"]["multiple"] == 3 for c in schema["components"])
    assert not any(a["field"] == "Profit target" for a in schema["assumptions"])
    strategy = yaml.safe_load(compile_schema_to_yaml(schema, market="NAS100", timeframe="1h"))
    assert [c["multiple"] for c in strategy["exit"]["long"] if c["type"] == "atr_sl"] == [2]
    assert [c["multiple"] for c in strategy["exit"]["long"] if c["type"] == "atr_tp"] == [3]
    assert not strategy_contract_issues(strategy)
