"""
Configure visualization elements and instantiate a server
"""

import altair as alt
import solara
import pandas as pd

from simulatingrisk.hawkdove.model import (
    Play,
    divergent_colors_10,
    HawkDoveModel,
)


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
    # specific to multiple risk attitude variant
    if hasattr(agent, "risk_level_changed"):
        portrayal["risk_level_changed"] = agent.risk_level_changed

    # color based on risk level; risk levels are always 0-9
    colors = divergent_colors_10

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

neighborhood_sizes = sorted(list(HawkDoveModel.neighborhood_sizes))

# parameters common to both hawk/dove variants
common_jupyterviz_params = {
    "grid_size": {
        "type": "SliderInt",
        "value": grid_size,
        "label": "Grid Size",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "play_neighborhood": {
        "type": "Select",
        "value": 8,
        "values": neighborhood_sizes,
        "label": "Play neighborhood size",
    },
    "observed_neighborhood": {
        "type": "Select",
        "value": 8,
        "values": neighborhood_sizes,
        "label": "Observed neighborhood (determines choice of play)",
    },
    "hawk_odds": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Hawk Odds (first choice)",
        "min": 0.0,
        "max": 1.0,
        "step": 0.1,
    },
    "random_play_odds": {
        "type": "SliderFloat",
        "value": 0.01,
        "label": "Random play odds",
        "min": 0.0,
        "max": 1.0,
        "step": 0.01,
    },
}

# in single-risk variant, risk level is set for all agents at init time
jupyterviz_params = common_jupyterviz_params.copy()
jupyterviz_params["agent_risk_level"] = {
    "type": "SliderInt",
    "label": "Agent risk attitude",
    "min": 0,
    "max": 8,
    "step": 1,
    "value": 2,
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

    # optionally display information from multi-risk attitude variant
    if "risk_level_changed" in df.columns:
        outer_color = alt.Color(
            "risk_level_changed", title="adjusted risk attitude"
        ).scale(
            domain=[False, True],
            range=["transparent", "black"],
        )
    else:
        outer_color = chart_color

    agent_chart = (
        alt.Chart(df)
        .mark_point()  # filled=True)
        .encode(
            x=alt.X("x", axis=None),  # no x-axis label
            y=alt.Y("y", axis=None),  # no y-axis label
            size=alt.Size("size", title="points rank"),  # relabel size for legend
            # when fill and color differ, color acts as an outline
            fill=chart_color,
            color=outer_color,
            shape=alt.Shape(  # use shape to indicate choice
                "choice", scale=alt.Scale(domain=hawkdove_domain, range=shape_range)
            ),
        )
        .configure_view(strokeOpacity=0)  # hide grid/chart lines
    )

    return solara.FigureAltair(agent_chart)
