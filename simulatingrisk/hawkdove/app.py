# solara/jupyterviz app
from mesa.experimental import JupyterViz

from simulatingrisk.hawkdove.model import HawkDoveModel
from simulatingrisk.hawkdove.server import (
    agent_portrayal,
    jupyterviz_params,
    draw_hawkdove_agent_space,
)


page = JupyterViz(
    HawkDoveModel,
    jupyterviz_params,
    measures=[],
    # measures=[plot_risk_histogram],
    name="Hawk/Dove with risk attitudes",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)
# required to render the visualization with Jupyter/Solara
page
