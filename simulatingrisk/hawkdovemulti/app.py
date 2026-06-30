from simulatingrisk.hawkdove.server import (
    common_jupyterviz_params,
    neighborhood_sizes,
)
from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel

# start with common hawk/dove params, then add params for variable risk
jupyterviz_params_var = common_jupyterviz_params.copy()
jupyterviz_params_var.update(
    {
        "risk_adjustment": {
            "type": "Select",
            "value": "adopt",
            "values": ["none", "adopt", "average"],
            "description": "If and how agents update their risk attitude",
        },
        "risk_distribution": {
            "type": "Select",
            "value": "uniform",
            "values": HawkDoveMultipleRiskModel.risk_distribution_options,
            "description": "Distribution for initial risk attitudes",
        },
        "include_endpoints": {
            "label": "Include risk attitudes 0 and 9",
            "type": "Checkbox",
            "value": True,
            "description": "Include 0/9 risk attitudes",
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
        "adjust_neighborhood": {
            "type": "Select",
            "value": 8,
            "values": neighborhood_sizes,
            "label": "Adjustment neighborhood size",
        },
        "adjust_payoff": {
            "type": "Select",
            "label": "Adjustment comparison period",
            "value": "recent",
            "values": HawkDoveMultipleRiskModel.supported_adjust_payoffs,
            "description": "Compare recent payoff (since last adjustment "
            + "round) or total (cumulative from start) when adjusting risk attitudes",
        },
    }
)
