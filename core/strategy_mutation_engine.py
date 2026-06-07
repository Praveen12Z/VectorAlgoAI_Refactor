# core/strategy_mutation_engine.py

from copy import deepcopy


def generate_mutations(cfg, optimizer=None, root_cause=None):
    """
    Mutation Engine V2:
    Creates strategy variants based on known weakness patterns.
    Still rule-based for now. Later GPT/Universal Engine will generate these dynamically.
    """

    mutations = []

    mutations.append({
        "name": "Original Strategy",
        "description": "Baseline unchanged strategy.",
        "config": deepcopy(cfg),
    })

    # Mutation 1: More conservative RSI filter
    try:
        m1 = deepcopy(cfg)

        for ind in m1.indicators:
            if getattr(ind, "name", "") == "rsi14":
                ind.period = 21

        mutations.append({
            "name": "RSI Smoothing Variant",
            "description": "Uses RSI 21 instead of RSI 14 to reduce noisy entries.",
            "config": m1,
        })

    except Exception:
        pass

    # Mutation 2: Stronger trend filter
    try:
        m2 = deepcopy(cfg)

        for ind in m2.indicators:
            if getattr(ind, "name", "") == "ema50":
                ind.period = 100
                ind.name = "ema100"

        mutations.append({
            "name": "Stronger Trend Filter",
            "description": "Uses EMA100 instead of EMA50 to avoid weak trend conditions.",
            "config": m2,
        })

    except Exception:
        pass

    # Mutation 3: Slower major trend filter
    try:
        m3 = deepcopy(cfg)

        for ind in m3.indicators:
            if getattr(ind, "name", "") == "ema200":
                ind.period = 300
                ind.name = "ema300"

        mutations.append({
            "name": "Macro Trend Filter",
            "description": "Uses EMA300 to trade only stronger macro trend environments.",
            "config": m3,
        })

    except Exception:
        pass

    # Mutation 4: Conservative copy for future rule tightening
    try:
        m4 = deepcopy(cfg)

        mutations.append({
            "name": "Conservative Risk Variant",
            "description": "Reserved conservative version for future stop/target optimization.",
            "config": m4,
        })

    except Exception:
        pass

    return mutations
