from copy import deepcopy


def generate_mutations(cfg):

    mutations = []

    # Original
    mutations.append(
        {
            "name": "Original",
            "config": deepcopy(cfg),
        }
    )

    # Variant A
    try:
        m1 = deepcopy(cfg)

        for ind in m1.indicators:
            if getattr(ind, "name", "") == "rsi14":
                ind.period = 21

        mutations.append(
            {
                "name": "RSI 21",
                "config": m1,
            }
        )
    except:
        pass

    # Variant B
    try:
        m2 = deepcopy(cfg)

        for ind in m2.indicators:
            if getattr(ind, "name", "") == "ema50":
                ind.period = 100

        mutations.append(
            {
                "name": "EMA 100 Filter",
                "config": m2,
            }
        )
    except:
        pass

    # Variant C
    try:
        m3 = deepcopy(cfg)

        mutations.append(
            {
                "name": "Conservative Variant",
                "config": m3,
            }
        )
    except:
        pass

    return mutations
