from core.component_executor import execute_component


def build_signals_from_schema(
    df,
    schema
):

    for component in schema["components"]:

        df = execute_component(
            df,
            component
        )

    return df
