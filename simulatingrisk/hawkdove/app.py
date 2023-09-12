# solara/jupyterviz app
from mesa.experimental import JupyterViz
import pandas as pd
import altair as alt
import solara

from simulatingrisk.hawkdove.model import HawkDoveModel
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

    chart = alt.Chart(df).mark_bar().encode(y="wealth", x="risk_level")
    return solara.FigureAltair(chart)


page = JupyterViz(
    HawkDoveModel,
    jupyterviz_params,
    # measures=[],
    measures=[plot_wealth],
    name="Hawk/Dove with risk attitudes",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)
# required to render the visualization with Jupyter/Solara
page
