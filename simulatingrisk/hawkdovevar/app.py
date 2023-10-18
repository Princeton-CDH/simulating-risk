# solara/jupyterviz app
from mesa.experimental import JupyterViz


from simulatingrisk.hawkdovevar.model import HawkDoveVariableRiskModel
from simulatingrisk.hawkdove.server import (
    agent_portrayal,
    jupyterviz_params,
    draw_hawkdove_agent_space,
)
from simulatingrisk.hawkdove.app import plot_hawks

jupyterviz_params_var = jupyterviz_params.copy()
del jupyterviz_params_var["agent_risk_level"]

page = JupyterViz(
    HawkDoveVariableRiskModel,
    jupyterviz_params_var,
    measures=[plot_hawks],
    name="Hawk/Dove game with variable risk attitudes",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)
# required to render the visualization with Jupyter/Solara
page
