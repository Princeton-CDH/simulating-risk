import math

import mesa
from simulatingrisk.risky_bet.model import divergent_colors


def risk_index(risk_level):
    """Calculate a risk bin index for a given risk level.
    Risk levels range from 0.0 to 1.0,
    Implement eleven bins, with bins for 0 - 0.05 and 0.95 - 1.0,
    since risk = 0, 0.5, and 1 are all special cases we want clearly captured.
    """
    # implementation adapted from https://stackoverflow.com/a/64995801/9706217

    # if we think of it as a range from -0.05 to 1.05,
    # then we can work with evenly sized 0.1 bins
    minval = -0.05
    binwidth = 0.1
    nbins = 11
    # Determine which bin this risk level belongs in
    binnum = int((risk_level - minval) // binwidth)  # // = floor division
    # convert bin number to 0-based index
    return min(nbins - 1, binnum)


def agent_portrayal(agent):
    # initial display
    portrayal = {
        # styles for mesa runserver
        "Shape": "circle",
        "Color": "gray",
        "Filled": "true",
        "Layer": 0,
        "r": 0.5,
        # styles for solara / jupyterviz
        "size": 25,
        "color": "tab:gray",
    }

    # color based on risk level, with ten bins
    # convert 0.0 to 1.0 to 1 - 10
    color_index = math.floor(agent.risk_level * 10)
    portrayal["color"] = "%s" % divergent_colors[color_index]
    # runserver requires uppercase; duplicate for now
    portrayal["Color"] = portrayal["color"]

    # size based on wealth within current distribution
    max_wealth = agent.model.max_agent_wealth
    wealth_index = math.floor(agent.wealth / max_wealth * 10)
    # set radius based on wealth, but don't go smaller than 1 radius
    # or too large to fit in the grid
    portrayal["r"] = (wealth_index / 15) + 0.1
    # size for solara / jupyterviz
    portrayal["size"] = (wealth_index / 15) * 50

    # TODO: change shape based on number of times risk level has been adjusted?
    # can't find a list of available shapes; setting to triangle and square
    # results in a 404 for a local custom url
    # NOTE: matplotlib scatter supports different shapes/markers,
    # but not in a single scatter plot; would need to be plotted in groups

    return portrayal


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

jupyterviz_params = {
    # "grid_size": grid_size,
    "grid_size": {
        "type": "SliderInt",
        "value": 20,
        "label": "Grid Size",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "risk_adjustment": {
        "type": "Select",
        "value": "adopt",
        "values": ["adopt", "average"],
        "description": "How agents update their risk level",
    },
}
