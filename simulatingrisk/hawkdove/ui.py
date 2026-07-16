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

#: ui options for grid size - 72 ~= current max that can render in marimo
grid_size_opts = MinMaxDefault(min=10, max=72, default=10, step=1)

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
        include_input=True,
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
    grid = model.grid._grid
    all_agent_data = []
    for i, col in enumerate(grid):
        for j, content in enumerate(col):
            if not content:
                continue
            agents = content if hasattr(content, "__iter__") else [content]
            for agent in agents:
                data = agent_portrayal(agent)
                data["x"] = i
                data["y"] = j
                all_agent_data.append(data)

    df = pd.DataFrame(all_agent_data)
    # drop mesa runserver fields not used in the Altair chart
    df.drop(columns=["Shape", "Layer", "r"], errors="ignore", inplace=True)
    # shorten field names — they repeat per-record in inline JSON
    df.rename(
        columns={
            "risk_level": "rl",
            "risk_level_changed": "rlc",
            "size": "s",
            "choice": "c",
        },
        inplace=True,
    )

    # encode categoricals as integers and round floats to reduce inline JSON size
    df["c"] = df["c"].map({"hawk": 1, "dove": 0})
    df["s"] = df["s"].round(1)

    # use grid x,y coordinates to plot, but suppress axis labels

    # currently passing in actual colors, not a variable to use for color
    # use domain/range to use color for display
    hawkdove_domain = (1, 0)  # hawk=1, dove=0
    shape_range = ("triangle-up", "circle")

    # when risk attitude is variable,
    # use divergent color scheme to indicate risk level
    if model.risk_attitudes == "variable":
        risk_attitude_domain = list(
            range(model.min_risk_level, model.max_risk_level + 1)
        )
        chart_color = (
            # set to nominal to show all values
            alt.Color("rl", title=["Risk", "Attitude"], type="nominal")
            # display discrete symbols rather than gradient
            .legend(orient="left", type="symbol")
            .scale(domain=risk_attitude_domain, range=divergent_colors_10)
        )
    elif model.risk_attitudes == "single":
        chart_color = (
            alt.Color("c", title="Play Choice")
            # .legend(None)
            .legend(labelExpr="datum.value === 1 ? 'hawk' : 'dove'")
            .scale(domain=hawkdove_domain, range=["orange", "blue"])
        )

    # optionally display information from multi-risk attitude variant
    if "rlc" in df.columns:
        # map true/false to 1/0 for compact JSON; drop rlc since only raa is encoded
        df["raa"] = df["rlc"].map({True: 1, False: 0})
        df.drop(columns=["rlc"], inplace=True)
        outer_color = (
            alt.Color(
                # use list to split legend title across two lines, for brevity
                "raa",
                title=["Adjusted", "Risk Attitude"],
                type="nominal",
            )
            .scale(
                domain=[1, 0],
                range=["black", "transparent"],
            )
            .legend(labelExpr="datum.value === 1 ? 'adjusted' : \"didn't adjust\"")
        )
    else:
        outer_color = chart_color

    renderer = "canvas" if model.grid.width * model.grid.height > 500 else "svg"
    agent_chart = (
        alt.Chart(df)
        .mark_point()  # filled=True)
        .encode(
            # scale=alt.Scale(padding=2, nice=False, zero=False
            x=alt.X("x", axis=None, scale=alt.Scale(nice=False, zero=False)),
            y=alt.Y("y", axis=None, scale=alt.Scale(nice=False, zero=False)),
            size=alt.Size("s", title="Payoff Rank"),  # relabel size for legend
            # when fill and color differ, color acts as an outline
            fill=chart_color,
            color=outer_color,
            shape=alt.Shape(  # use shape to indicate choice
                "c",
                title="Play Choice",
                scale=alt.Scale(domain=hawkdove_domain, range=shape_range),
                legend=alt.Legend(labelExpr="datum.value === 1 ? 'hawk' : 'dove'"),
            ),
        )
        .configure(padding=5)
        .configure_view(strokeOpacity=0)  # hide grid/chart lines
        .properties(usermeta={"embedOptions": {"renderer": renderer}})
    )

    return agent_chart
