import mesa

from simulatingrisk.risky_bet.model import RiskyBetModel, divergent_colors


def agent_portrayal(agent):
    import math
    from simulatingrisk.risky_bet.model import divergent_colors

    portrayal = {
        "Shape": "circle",
        "Color": "gray",
        "Filled": "true",
        "Layer": 0,
        "r": 0.5,
    }

    # color based on risk level, with ten bins
    # convert 0.0 to 1.0 to 1 - 10
    color_index = math.floor(agent.risk_level * 10)
    portrayal["Color"] = divergent_colors[color_index]

    # size based on wealth
    # TODO: make this more of a gradient
    if agent.wealth > agent.model.initial_wealth / 2:
        portrayal["r"] = 0.2
    elif math.isclose(agent.wealth, agent.model.initial_wealth, abs_tol=100):
        portrayal["r"] = 0.4
    else:
        portrayal["r"] = 0.7
    return portrayal


grid_size = 10

colors = [
    "#a50026",
    "#d73027",
    "#f46d43",
    "#fdae61",
    "#fee08b",
    "#d9ef8b",
    "#a6d96a",
    "#66bd63",
    "#1a9850",
    "#006837",
]

grid = mesa.visualization.CanvasGrid(agent_portrayal, grid_size, grid_size, 500, 500)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "risk_min", "Color": divergent_colors[0]},
        {"Label": "risk_q1", "Color": divergent_colors[3]},
        {"Label": "risk_mean", "Color": divergent_colors[5]},
        {"Label": "risk_q3", "Color": divergent_colors[7]},
        {"Label": "risk_max", "Color": divergent_colors[-1]},
    ],
    data_collector_name="datacollector",
)

server = mesa.visualization.ModularServer(
    RiskyBetModel,
    [grid, chart],
    "Risky Bet Simulation",
    {"grid_size": grid_size},
)
server.port = 8521  # The default
server.launch()
