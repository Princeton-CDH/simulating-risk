import mesa
from mesa.visualization.ModularVisualization import VisualizationElement, CHART_JS_FILE
import numpy as np


chart = mesa.visualization.ChartModule(
    [
        {"Label": "prob_notcontaminated", "Color": "blue"},
        {"Label": "contaminated", "Color": "red"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,  # default height is 200
)
risk_chart = mesa.visualization.ChartModule(
    [
        {"Label": "average_risk_level", "Color": "blue"},
        {"Label": "min_risk_level", "Color": "green"},
        {"Label": "max_risk_level", "Color": "orange"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,
)

total_agent_chart = mesa.visualization.ChartModule(
    [
        {"Label": "num_agents", "Color": "gray"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,
)


# histogram chart from mesa tutorial
# https://mesa.readthedocs.io/en/stable/tutorials/adv_tutorial_legacy.html
class RiskHistogramModule(VisualizationElement):
    package_includes = [CHART_JS_FILE]
    local_includes = ["HistogramModule.js"]

    def __init__(self, bins, canvas_height, canvas_width, label):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.bins = bins
        new_element = "new HistogramModule({}, {}, {}, {})"
        new_element = new_element.format(
            bins, canvas_width, canvas_height, '"%s"' % label
        )
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        risk_levels = [agent.risk_level for agent in model.schedule.agents]
        # generate a histogram of risk levels based on the specified bins
        hist = np.histogram(risk_levels, bins=self.bins)[0]
        return [int(x) for x in hist]


# bins for risk levels to chart as histogram
# match types used in the class, i.e. 0, 0.1, 0.2, 0.3, ... 1.0
# NOTE: if we don't include 1.1, np.histogram groups 0.9 with 1.0
risk_bins = [r / 10 for r in range(12)]
histogram = RiskHistogramModule(risk_bins, 200, 500, "risk levels")

# server is initialized in run.py
