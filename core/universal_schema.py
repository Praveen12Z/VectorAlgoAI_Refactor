class UniversalStrategy:

    def __init__(self):

        self.components = []

    def add_component(
        self,
        category,
        component,
        params=None
    ):

        self.components.append({

            "category": category,
            "component": component,
            "params": params or {}
        })

    def to_dict(self):

        return {
            "components": self.components
        }
