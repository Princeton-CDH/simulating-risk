import os
import numpy as np

from mesa.visualization.ModularVisualization import VisualizationElement, CHART_JS_FILE


# histogram chart from mesa tutorial
# https://mesa.readthedocs.io/en/stable/tutorials/adv_tutorial_legacy.html
class RiskHistogramModule(VisualizationElement):
    package_includes = [CHART_JS_FILE]
    local_includes = ["histogram.js"]
    # javascript is located in the same file as this python file
    local_dir = os.path.dirname(os.path.realpath(__file__))

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
