"""
Configure visualization elements and instantiate a server
"""

import altair as alt
import solara
import pandas as pd

from simulatingrisk.hawkdove.model import Play, divergent_colors_9, divergent_colors_5


def agent_portrayal(agent):
    # initial display
    portrayal = {
        # styles for mesa runserver
        "Shape": "circle",
        # "Color": "gray",
        # "Filled": "true",
        "Layer": 0,
        "r": 0.2,
        "risk_level": agent.risk_level,
        "choice": str(agent.choice),
        # styles for solara / jupyterviz
        "size": 25,
        # "color": "tab:gray",
    }

    # color based on risk level
    if agent.model.include_diagonals:
        colors = divergent_colors_9
    else:
        colors = divergent_colors_5

    portrayal["Color"] = colors[agent.risk_level]
    # copy to lowercase color for solara
    portrayal["color"] = portrayal["Color"]

    # filled for hawks, hollow for doves
    # (shapes would be better...)
    portrayal["Filled"] = agent.choice == Play.HAWK
    portrayal["choice"] = "hawk" if agent.choice == Play.HAWK else "dove"

    # size based on points within current distribution after first round
    if agent.points > 0:
        # # set radius based on relative points, but don't go smaller than 1 radius
        # # or too large to fit in the grid
        portrayal["r"] = (agent.points_rank / 15) + 0.2
        # # size for solara / jupyterviz
        portrayal["size"] = (agent.points_rank / 15) * 50

    return portrayal


grid_size = 10

model_params = {
    "grid_size": grid_size,
}


jupyterviz_params = {
    "grid_size": {
        "type": "SliderInt",
        "value": grid_size,
        "label": "Grid Size",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "include_diagonals": {
        "type": "Checkbox",
        "value": True,
        "label": "Include diagonal neighbors",
    },
    "risk_attitudes": {
        "type": "Select",
        "value": "variable",
        "values": ["variable", "single"],
        "description": "Agent initial risk level",
    },
    "agent_risk_level": {
        "type": "SliderInt",
        "min": 0,
        "max": 8,
        "step": 1,
        "value": 2,
    },
    "hawk_odds": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Hawk Odds (first choice)",
        "min": 0.0,
        "max": 1.0,
        "step": 0.1,
    },
    # "risk_adjustment": {
    #     "type": "Select",
    #     "value": "adopt",
    #     "values": ["adopt", "average"],
    #     "description": "How agents update their risk level",
    # },
}


def draw_hawkdove_agent_space(model, agent_portrayal):
    # custom agent space chart, modeled on default
    # make_space method in mesa jupyterviz code,
    # but using altair so we can contrl shapes as well as color and size
    all_agent_data = []
    for i in range(model.grid.width):
        for j in range(model.grid.height):
            agent_data = {}
            content = model.grid._grid[i][j]
            if not content:
                continue
            if not hasattr(content, "__iter__"):
                # Is a single grid
                content = [content]
            for agent in content:
                # use all data from agent portrayal, and add x,y coordinates
                agent_data = agent_portrayal(agent)
                agent_data["x"] = i
                agent_data["y"] = j
            all_agent_data.append(agent_data)

    df = pd.DataFrame(all_agent_data)
    # print(all_agent_data)

    # use grid x,y coordinates to plot, but supress axis labels

    # currently passing in actual colors, not a variable to use for color
    # use domain/range to use color for display
    hawkdove_domain = ("hawk", "dove")
    shape_range = ("triangle-up", "circle")

    # when risk attitude is variable,
    # use divergent color scheme to indicate risk level
    if model.risk_attitudes == "variable":
        colors = list(set(a["color"] for a in all_agent_data))
        chart_color = alt.Color("color").legend(None).scale(domain=colors, range=colors)
    elif model.risk_attitudes == "single":
        chart_color = (
            alt.Color("choice")
            # .legend(None)
            .scale(domain=hawkdove_domain, range=["orange", "blue"])
        )

    chart = (
        alt.Chart(df)
        .mark_point(filled=True)
        .encode(
            x=alt.X("x", axis=None),  # no x-axis label
            y=alt.Y("y", axis=None),  # no y-axis label
            size=alt.Size("size", title="points rank"),  # relabel size for legend
            color=chart_color,
            shape=alt.Shape(  # use shape to indicate choice
                "choice", scale=alt.Scale(domain=hawkdove_domain, range=shape_range)
            ),
        )
        .configure_view(strokeOpacity=0)  # hide grid/chart lines
    )
    return solara.FigureAltair(chart)
