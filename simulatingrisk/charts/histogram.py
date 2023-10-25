import os

import numpy as np
import solara
from matplotlib.figure import Figure


from mesa.visualization.ModularVisualization import VisualizationElement, CHART_JS_FILE


# histogram chart from mesa tutorial
# https://mesa.readthedocs.io/en/stable/tutorials/adv_tutorial_legacy.html
class HistogramModule(VisualizationElement):
    """histogram plot of agent risk levels; for use with mesa runserver"""

    package_includes = [CHART_JS_FILE]
    local_includes = ["histogram.js"]
    # javascript is located in the same file as this python file
    local_dir = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, bins, canvas_height, canvas_width, label, agent_attr):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.bins = bins
        self.agent_attr = agent_attr
        new_element = "new HistogramModule({}, {}, {}, {})"
        new_element = new_element.format(
            bins, canvas_width, canvas_height, '"%s"' % label
        )
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        agent_values = [
            getattr(agent, self.agent_attr) for agent in model.schedule.agents
        ]
        # generate a histogram of risk levels based on the specified bins
        hist = np.histogram(agent_values, bins=self.bins)[0]
        return [int(x) for x in hist]


class RiskHistogramModule(HistogramModule):
    """special case: risk_level histogram"""

    def __init__(self, bins, canvas_height, canvas_width, label="risk levels"):
        super().__init__(
            bins, canvas_height, canvas_width, label, agent_attr="risk_level"
        )


# generate bins for histogram, capturing 0-0.5 and 0.95-1.0
risk_bins = []
r = 0.05
while r < 1.05:
    risk_bins.append(round(r, 2))
    r += 0.1


def plot_risk_histogram(model):
    """histogram plot of agent risk levels; for use with jupyterviz/solara"""

    # adapted from mesa visualiation tutorial
    # https://mesa.readthedocs.io/en/stable/tutorials/visualization_tutorial.html#Building-your-own-visualization-component

    # Note: per Mesa docs, has to be initialized using this method instead of
    # plt.figure(), for thread safety purpose
    fig = Figure()
    ax = fig.subplots()
    # generate a histogram of current risk levels
    risk_levels = [agent.risk_level for agent in model.schedule.agents]
    ax.hist(risk_levels, bins=risk_bins)
    ax.set_title("risk levels")
    solara.FigureMatplotlib(fig)
