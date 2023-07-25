import mesa

from simulatingrisk.charts.histogram import RiskHistogramModule

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


# bins for risk levels to chart as histogram
# match types used in the class, i.e. 0, 0.1, 0.2, 0.3, ... 1.0
# NOTE: if we don't include 1.1, np.histogram groups 0.9 with 1.0
risk_bins = [r / 10 for r in range(12)]
histogram = RiskHistogramModule(risk_bins, 200, 500, "risk levels")

# server is initialized in run.py
