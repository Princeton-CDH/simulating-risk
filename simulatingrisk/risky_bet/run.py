import mesa

from simulatingrisk.risky_bet.model import RiskyBetModel, divergent_colors
from simulatingrisk.risky_bet.server import agent_portrayal, grid_size, model_params
from simulatingrisk.charts.histogram import RiskHistogramModule, risk_bins
from simulatingrisk.utils import labelLabel

grid = mesa.visualization.CanvasGrid(agent_portrayal, grid_size, grid_size, 500, 500)


risk_chart = mesa.visualization.ChartModule(
    labelLabel(
        [
            {"Label": "risk_min", "Color": divergent_colors[0]},
            {"Label": "risk_q1", "Color": divergent_colors[3]},
            {"Label": "risk_mean", "Color": divergent_colors[5]},
            {"Label": "risk_q3", "Color": divergent_colors[7]},
            {"Label": "risk_max", "Color": divergent_colors[-1]},
        ]
    ),
    data_collector_name="datacollector",
    canvas_height=100,
)

world_chart = mesa.visualization.ChartModule(
    labelLabel(
        [
            {"Label": "prob_risky_payoff", "Color": "gray"},
            {"Label": "risky_bet", "Color": "blue"},
        ]
    ),
    data_collector_name="datacollector",
    canvas_height=100,
)


histogram = RiskHistogramModule(risk_bins, 175, 500, "risk levels")

server = mesa.visualization.ModularServer(
    RiskyBetModel,
    [grid, histogram, world_chart, risk_chart],
    "Risky Bet Simulation",
    model_params=model_params,
)
server.port = 8521  # The default
server.launch()
