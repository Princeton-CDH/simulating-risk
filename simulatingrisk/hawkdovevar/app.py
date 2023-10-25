# solara/jupyterviz app
from mesa.experimental import JupyterViz


from simulatingrisk.hawkdovevar.model import HawkDoveVariableRiskModel
from simulatingrisk.hawkdove.server import (
    agent_portrayal,
    common_jupyterviz_params,
    draw_hawkdove_agent_space,
)
from simulatingrisk.hawkdove.app import plot_hawks

# start with common hawk/dove params, then add params for variable risk
jupyterviz_params_var = common_jupyterviz_params.copy()
jupyterviz_params_var.update(
    {
        "risk_adjustment": {
            "type": "Select",
            "value": "adopt",
            "values": ["none", "adopt", "average"],
            "description": "If and how agents update their risk level",
        },
        "adjust_every": {
            "label": "Adjustment frequency (# rounds)",
            "type": "SliderInt",
            "min": 1,
            "max": 30,
            "step": 1,
            "value": 10,
            "description": "How many rounds between risk adjustment",
        },
    }
)

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
