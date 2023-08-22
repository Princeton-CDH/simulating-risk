# solara/jupyterviz app
from mesa.experimental import JupyterViz

from simulatingrisk.risky_bet.model import RiskyBetModel
from simulatingrisk.risky_bet.server import (
    agent_portrayal,
    jupyterviz_params,
    make_histogram,
)

page = JupyterViz(
    RiskyBetModel,
    jupyterviz_params,
    measures=[make_histogram],
    name="Risky Bet",
    agent_portrayal=agent_portrayal,
)
# required to render the visualization with Jupyter/Solara
page
