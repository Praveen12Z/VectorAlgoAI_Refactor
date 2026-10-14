import pytest
import yaml

from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.strategy_config import parse_strategy_yaml


def compile_text(text):
    return yaml.safe_load(compile_schema_to_yaml(build_strategy_from_text(text)))


def test_exact_ema_rsi_parameters_survive_compilation():
    strategy = compile_text("Buy when EMA 12 above EMA 36 and RSI above 62")
    indicators = {i["name"]: i["period"] for i in strategy["indicators"]}
    assert indicators["ema20"] == 12
    assert indicators["ema50"] == 36
    assert strategy["entry"]["long"][1]["right"] == 62
    assert len(strategy["entry"]["long"]) == 2
    assert parse_strategy_yaml(yaml.safe_dump(strategy)).raw == strategy


@pytest.mark.parametrize("text", [
    "EMA 20 crosses above EMA 50 and RSI above 50",
    "EMA 20 above EMA 50 and RSI above 50 with news filter",
    "EMA 20 above EMA 50 and RSI above 50 with support",
    "EMA 20 above EMA 50 and RSI above 50 and volume above average",
    "EMA 20 above EMA 50 and RSI above 50 and stop loss 1%",
    "EMA 20 above EMA 50 and RSI above 50 and short below support",
])
def test_unsupported_or_unrecognized_instructions_fail(text):
    with pytest.raises(ValueError):
        compile_text(text)


def test_bad_ema_periods_fail():
    with pytest.raises(ValueError):
        compile_text("EMA 50 above EMA 20 and RSI above 50")


def test_bad_rsi_threshold_fails():
    with pytest.raises(ValueError):
        compile_text("EMA 20 above EMA 50 and RSI above 120")


def test_missing_conditions_fail():
    with pytest.raises(ValueError):
        compile_text("EMA 20 above EMA 50")


def test_compiler_rejects_unsupported_schema_component():
    schema = {"components": [
        {"component": "ema_trend", "params": {"fast": 20, "slow": 50}},
        {"component": "rsi_filter", "params": {"threshold": 50}},
        {"component": "news_filter", "params": {}},
    ]}
    with pytest.raises(ValueError, match="Unsupported"):
        compile_schema_to_yaml(schema)
