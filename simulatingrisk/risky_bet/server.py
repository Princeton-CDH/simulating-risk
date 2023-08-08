import mesa
import solara
from matplotlib.figure import Figure


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
    import math
    from simulatingrisk.risky_bet.model import divergent_colors

    # initial display
    portrayal = {
        "Shape": "circle",
        "Color": "tab:gray",
        "Filled": "true",
        "Layer": 0,
        "r": 0.5,
    }

    # color based on risk level, with ten bins
    # convert 0.0 to 1.0 to 1 - 10
    color_index = math.floor(agent.risk_level * 10)
    portrayal["Color"] = "rgb:%s" % divergent_colors[color_index]

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

# generate bins for histogram, capturing 0-0.5 and 0.95-1.0
risk_bins = []
r = 0.05
while r < 1.05:
    risk_bins.append(round(r, 2))
    r += 0.1


# jupyter histogram based on mesa tutorial


def make_histogram(viz):
    # Note: you must initialize a figure using this method instead of
    # plt.figure(), for thread safety purpose
    fig = Figure()
    ax = fig.subplots()
    # generate a histogram of risk levels
    risk_levels = [agent.risk_level for agent in viz.model.schedule.agents]
    # Note: you have to use Matplotlib's OOP API instead of plt.hist
    # because plt.hist is not thread-safe.
    ax.hist(risk_levels, bins=risk_bins)
    # You have to specify the dependencies as follows, so that the figure
    # auto-updates when viz.model or viz.df is changed.
    solara.FigureMatplotlib(fig, dependencies=[viz.model, viz.df])
