# solara/jupyterviz app
from mesa.experimental import JupyterViz

from simulatingrisk.risky_food.model import RiskyFoodModel
from simulatingrisk.risky_food.server import (
    jupyterviz_params,
    plot_total_agents,
)
from simulatingrisk.charts.histogram import plot_risk_histogram

page = JupyterViz(
    RiskyFoodModel,
    jupyterviz_params,
    measures=[plot_total_agents, plot_risk_histogram],
    name="Risky Food",
    space_drawer=False,  # no agent portrayal because this model does not use a grid
)
# required to render the visualization with Jupyter/Solara
page
