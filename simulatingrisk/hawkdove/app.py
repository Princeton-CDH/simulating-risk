# solara/jupyterviz app
from mesa.experimental import JupyterViz
import pandas as pd
import altair as alt
import solara


from simulatingrisk.hawkdove.model import HawkDoveSingleRiskModel
from simulatingrisk.hawkdove.server import (
    agent_portrayal,
    jupyterviz_params,
    draw_hawkdove_agent_space,
)


def plot_wealth(model):
    """histogram plot of agent wealth levels across risk levels;
    for use with jupyterviz/solara"""

    # generate a histogram of points across risk levels
    risk_wealth = [(agent.risk_level, agent.points) for agent in model.schedule.agents]
    df = pd.DataFrame(risk_wealth, columns=["risk_level", "wealth"])

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(y="wealth", x=alt.X("risk_level", title="risk attitude"))
    )
    return solara.FigureAltair(chart)


def plot_hawks(model):
    """plot percent of agents who chose hawk over last several rounds;
    for use with jupyterviz/solara"""

    model_df = model.datacollector.get_model_vars_dataframe().reset_index()

    # limit to last N rounds (how many ?)
    last_n_rounds = model_df.tail(50)
    # determine domain of the chart;
    # starting domain 0-50 so it doesn't jump / expand as much
    max_index = max(model_df.last_valid_index() or 0, 50)
    min_index = max(max_index - 50, 0)

    bar_chart = (
        alt.Chart(last_n_rounds)
        .mark_bar(color="orange")
        .encode(
            x=alt.X(
                "index", title="Step", scale=alt.Scale(domain=[min_index, max_index])
            ),
            y=alt.Y(
                "percent_hawk",
                title="Percent who chose hawk",
                scale=alt.Scale(domain=[0, 1]),
            ),
        )
    )
    # graph rolling average as a line over the bar chart,
    # once we have enough rounds
    if model_df.rolling_percent_hawk.any():
        line = (
            alt.Chart(last_n_rounds)
            .mark_line(color="blue")
            .encode(
                x=alt.X("index", title="Step"),
                y=alt.Y(
                    "rolling_percent_hawk",
                    title="% hawk (rolling average)",
                    scale=alt.Scale(domain=[0, 1]),
                ),
            )
        )
        # add the rolling average line on top of the bar chart
        bar_chart += line

    return solara.FigureAltair(bar_chart)


page = JupyterViz(
    HawkDoveSingleRiskModel,
    jupyterviz_params,
    measures=[plot_hawks],
    name="Hawk/Dove game with risk attitudes; all agents have the same risk attitude",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)

# required to render the visualization with Jupyter/Solara
page
