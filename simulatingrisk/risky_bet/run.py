import mesa

from simulatingrisk.risky_bet.model import RiskyBetModel, divergent_colors
from simulatingrisk.risky_bet.server import agent_portrayal
from simulatingrisk.risky_food.server import RiskHistogramModule


grid_size = 20


# make model parameters user-configurable
model_params = {
    "grid_size": grid_size,  # mesa.visualization.StaticText(value=grid_size),
    # "grid_size": mesa.visualization.Slider(
    #     "Grid size",
    #     value=20,
    #     min_value=10,
    #     max_value=100,
    #     description="Grid dimension (n*n = number of agents)",
    # ),
    "risk_adjustment": mesa.visualization.Choice(
        "Risk adjustment strategy",
        value="adopt",
        choices=["adopt", "average"],
        description="How agents update their risk level",
    ),
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, grid_size, grid_size, 500, 500)

risk_chart = mesa.visualization.ChartModule(
    [
        {"Label": "risk_min", "Color": divergent_colors[0]},
        {"Label": "risk_q1", "Color": divergent_colors[3]},
        {"Label": "risk_mean", "Color": divergent_colors[5]},
        {"Label": "risk_q3", "Color": divergent_colors[7]},
        {"Label": "risk_max", "Color": divergent_colors[-1]},
    ],
    data_collector_name="datacollector",
    canvas_height=100,
)
world_chart = mesa.visualization.ChartModule(
    [
        {"Label": "prob_risky_payoff", "Color": "gray"},
        {"Label": "risky_bet", "Color": "blue"},
    ],
    data_collector_name="datacollector",
    canvas_height=100,
)


# generate bins for histogram, capturing 0-0.5 and 0.95-1.0
risk_bins = []
r = 0.05
while r < 1.05:
    risk_bins.append(round(r, 2))
    r += 0.1
histogram = RiskHistogramModule(risk_bins, 175, 500, "risk levels")


server = mesa.visualization.ModularServer(
    RiskyBetModel,
    [grid, histogram, world_chart, risk_chart],
    "Risky Bet Simulation",
    model_params=model_params,
)
server.port = 8521  # The default
server.launch()
