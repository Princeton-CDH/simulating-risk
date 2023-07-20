import mesa

from simulatingrisk.risky_bet.model import RiskyBetModel, divergent_colors
from simulatingrisk.risky_bet.server import agent_portrayal

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
)
world_chart = mesa.visualization.ChartModule(
    [
        {"Label": "prob_risky_payoff", "Color": "gray"},
        {"Label": "risky_bet", "Color": "blue"},
    ],
    data_collector_name="datacollector",
)
server = mesa.visualization.ModularServer(
    RiskyBetModel,
    [grid, risk_chart, world_chart],
    "Risky Bet Simulation",
    model_params=model_params,
)
server.port = 8521  # The default
server.launch()
