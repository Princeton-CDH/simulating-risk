import mesa

from simulatingrisk.risky_bet.model import RiskyBetModel, divergent_colors


def agent_portrayal(agent):
    import math
    from simulatingrisk.risky_bet.model import divergent_colors

    # initial display
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

    # size based on wealth within current distribution
    max_wealth = agent.model.max_agent_wealth
    wealth_index = math.floor(agent.wealth / max_wealth * 10)
    # set radius based on wealth, but don't go smaller than 0.1 radius
    # or too large to fit in the grid
    portrayal["r"] = wealth_index / 15 + 0.1

    # TODO: change shape based on number of times risk level has been adjusted?
    # can't find a list of available shapes; setting to triangle and square
    # results in a 404 for a local custom url

    return portrayal


grid_size = 20

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
    model_params=model_params,
)
server.port = 8521  # The default
server.launch()
