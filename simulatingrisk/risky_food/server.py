import mesa
import solara
from matplotlib.figure import Figure

from simulatingrisk.charts.histogram import RiskHistogramModule
from simulatingrisk.utils import labelLabel


chart = mesa.visualization.ChartModule(
    labelLabel(
        [
            {"Label": "prob_notcontaminated", "Color": "blue"},
            {"Label": "contaminated", "Color": "red"},
        ]
    ),
    data_collector_name="datacollector",
    canvas_height=100,  # default height is 200
)
risk_chart = mesa.visualization.ChartModule(
    labelLabel(
        [
            {"Label": "average_risk_level", "Color": "blue"},
            {"Label": "min_risk_level", "Color": "green"},
            {"Label": "max_risk_level", "Color": "orange"},
        ]
    ),
    data_collector_name="datacollector",
    canvas_height=100,
)

total_agent_chart = mesa.visualization.ChartModule(
    labelLabel(
        [
            {"Label": "num_agents", "Color": "gray"},
        ]
    ),
    data_collector_name="datacollector",
    canvas_height=100,
)


# bins for risk levels to chart as histogram
# match types used in the class, i.e. 0, 0.1, 0.2, 0.3, ... 1.0
# NOTE: if we don't include 1.1, np.histogram groups 0.9 with 1.0
risk_bins = [r / 10 for r in range(12)]
histogram = RiskHistogramModule(risk_bins, 200, 500, "risk levels")

# server is initialized in run.py
# jupyterviz is initialized in app.py


jupyterviz_params = {
    "n": {
        "type": "SliderInt",
        "value": 20,
        "label": "Number of starting agents",
        "min": 10,
        "max": 50,
        "step": 1,
    },
    "mode": {
        "type": "Select",
        "value": "types",
        "values": ["types", "random"],
        "description": "Risk types of random risk level distribution",
    },
}


def plot_total_agents(model):
    """plot total agents over time to provide an indicator of population size"""
    fig = Figure()
    ax = fig.subplots()
    # generate a line plot of total number of agents
    model_df = model.datacollector.get_model_vars_dataframe()
    ax.plot(model_df.num_agents)
    ax.set_title("total agents")
    solara.FigureMatplotlib(fig)
