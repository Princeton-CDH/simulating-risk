"""
Configure visualization elements and instantiate a server
"""

from collections import namedtuple

import altair as alt
import pandas as pd
import marimo as mo

from simulatingrisk.hawkdove.model import (
    HawkDoveModel,
    Play,
    divergent_colors_10,
)


def agent_portrayal(agent):
    # initial display
    portrayal = {
        # styles for mesa runserver
        "Shape": "circle",
        "Layer": 0,
        "r": 0.2,
        "risk_level": agent.risk_level,
        "choice": str(agent.choice),
        # styles for solara / jupyterviz
        "size": 25,
    }
    # specific to multiple risk attitude variant
    if hasattr(agent, "risk_level_changed"):
        portrayal["risk_level_changed"] = agent.risk_level_changed

    # color based on risk level; risk levels are always 0-9

    # (shapes would be better...)
    portrayal["choice"] = "hawk" if agent.choice == Play.HAWK else "dove"

    # size based on points within current distribution after first round
    if agent.points > 0:
        # set radius based on relative points, but don't go smaller than 1 radius
        # or too large to fit in the grid
        portrayal["r"] = (agent.points_rank / 15) + 0.2
        # size for solara / jupyterviz
        portrayal["size"] = (agent.points_rank / 15) * 50

    return portrayal


MinMaxDefault = namedtuple("MinMaxDefault", ["min", "max", "default", "step"])

#: ui options for grid size
grid_size_opts = MinMaxDefault(min=10, max=100, default=10, step=1)

#: supported neighborhood sizes
neighborhood_sizes = sorted(list(HawkDoveModel.neighborhood_sizes))
#: default neighborhood size
default_neighborhood_size = 8

#: ui options for hawk odds
hawk_odds_opts = MinMaxDefault(min=0.0, max=1.0, default=0.5, step=0.1)

#: ui options for random play odds
random_play_opts = MinMaxDefault(min=0.0, max=1.0, default=0.01, step=0.1)


#: ui controls for parameters common to both hawk/dove simulations
ui_controls = {
    # key = model parameter; value = marimo ui element
    # int slider with selected value visible
    "grid_size": mo.ui.slider(
        start=grid_size_opts.min,
        stop=grid_size_opts.max,
        step=grid_size_opts.step,
        value=grid_size_opts.default,
        label="Grid Size",
        show_value=True,
    ),
    # drop-down to select from choices
    "play_neighborhood": mo.ui.dropdown(
        options=neighborhood_sizes,
        label="Play neighborhood size",
        value=default_neighborhood_size,
    ),
    "observed_neighborhood": mo.ui.dropdown(
        options=neighborhood_sizes,
        label="Observed neighborhood (determines choice of play)",
        value=default_neighborhood_size,
    ),
    "hawk_odds": mo.ui.slider(
        start=hawk_odds_opts.min,
        stop=hawk_odds_opts.max,
        step=hawk_odds_opts.step,
        value=hawk_odds_opts.default,
        label="Hawk Odds (first choice)",
        show_value=True,
    ),
    "random_play_odds": mo.ui.slider(
        start=random_play_opts.min,
        stop=random_play_opts.max,
        step=random_play_opts.step,
        value=random_play_opts.default,
        label="Random play odds",
        show_value=True,
    ),
}

# in single-risk variant, risk level is set for all agents at init time
singlerisk_controls = ui_controls.copy()
singlerisk_controls["agent_risk_level"] = mo.ui.slider(
    start=0,
    stop=8,
    step=1,
    value=2,
    label="Agent risk attitude",
    show_value=True,
)


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

    # use grid x,y coordinates to plot, but suppress axis labels

    # currently passing in actual colors, not a variable to use for color
    # use domain/range to use color for display
    hawkdove_domain = ("hawk", "dove")
    shape_range = ("triangle-up", "circle")

    # when risk attitude is variable,
    # use divergent color scheme to indicate risk level
    if model.risk_attitudes == "variable":
        risk_attitude_domain = list(
            range(model.min_risk_level, model.max_risk_level + 1)
        )
        chart_color = (
            # set to nominal to show all values
            alt.Color("risk_level", title=["Risk", "Attitude"], type="nominal")
            # display discrete symbols rather than gradient
            .legend(orient="left", type="symbol").scale(
                domain=risk_attitude_domain, range=divergent_colors_10
            )
        )
    elif model.risk_attitudes == "single":
        chart_color = (
            alt.Color("choice", title="Play Choice")
            # .legend(None)
            .scale(domain=hawkdove_domain, range=["orange", "blue"])
        )

    # optionally display information from multi-risk attitude variant
    if "risk_level_changed" in df.columns:
        # map true/false to readable labels for display in the chart
        df["risk_attitude_adjustment"] = df["risk_level_changed"].map(
            {True: "adjusted", False: "didn't adjust"}
        )

        outer_color = alt.Color(
            # use list to split legend title across two lines, for brevity
            "risk_attitude_adjustment",
            title=["Adjusted", "Risk Attitude"],
        ).scale(
            domain=["adjusted", "didn't adjust"],
            range=["black", "transparent"],
        )
    else:
        outer_color = chart_color

    agent_chart = (
        alt.Chart(df)
        .mark_point()  # filled=True)
        .encode(
            x=alt.X("x", axis=None),  # no x-axis label
            y=alt.Y("y", axis=None),  # no y-axis label
            size=alt.Size("size", title="Payoff Rank"),  # relabel size for legend
            # when fill and color differ, color acts as an outline
            fill=chart_color,
            color=outer_color,
            shape=alt.Shape(  # use shape to indicate choice
                "choice",
                title="Play Choice",
                scale=alt.Scale(domain=hawkdove_domain, range=shape_range),
            ),
        )
        .configure_view(strokeOpacity=0)  # hide grid/chart lines
    )

    return agent_chart
