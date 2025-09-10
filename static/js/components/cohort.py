from unfold.components import Component, register_component

@register_component
class CohortComponent(Component):
    class Media:
        js = ("js/components/CohortComponent.js",)  # static path

    template_name = "unfold/components/chart/cohort.html"

    def __init__(self, data=None, **kwargs):
        self.data = data or []
        super().__init__(**kwargs)

    def get_context_data(self, request=None):
        return {"data": self.data}
