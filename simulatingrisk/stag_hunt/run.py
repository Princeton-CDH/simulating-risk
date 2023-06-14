import mesa
from simulatingrisk.stag_hunt.model import StagHuntModel


def agent_portrayal(agent):
    # TODO: figure out where Mesa wants this import to happen
    # (expects model and server nested deeper than run?)
    from simulatingrisk.stag_hunt.model import HuntChoice

    portrayal = {
        "Shape": "circle",
        "Color": "gray",
        "Filled": "true",
        "Layer": 0,
        "r": 0.2,
    }

    if agent.hunting == HuntChoice.STAG:
        portrayal["Color"] = "green"
    else:
        portrayal["Color"] = "blue"

    if agent.last_payoff == 0:
        portrayal["r"] = 0.2
    elif agent.last_payoff == 3:
        portrayal["r"] = 0.4
    elif agent.last_payoff == 4:
        portrayal["r"] = 0.7
    return portrayal


grid = mesa.visualization.CanvasGrid(agent_portrayal, 20, 20, 500, 500)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "stag_hunters", "Color": "green"},
        {"Label": "hare_hunters", "Color": "blue"},
    ],
    data_collector_name="datacollector",
)

server = mesa.visualization.ModularServer(
    StagHuntModel, [grid, chart], "Stag Hunt Model", {"width": 20, "height": 20}
)
server.port = 8521  # The default
server.launch()
