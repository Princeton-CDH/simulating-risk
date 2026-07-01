import marimo as mo

from simulatingrisk.hawkdove.ui import default_neighborhood_size, neighborhood_sizes
from simulatingrisk.hawkdove.ui import ui_controls as base_ui_controls
from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel

# start with common hawk/dove ui controls, then add controls for multiple risk attitudes
ui_controls = base_ui_controls.copy()
ui_controls.update(
    {
        "risk_adjustment": mo.ui.dropdown(
            options=["none", "adopt", "average"],
            label="Risk adjustment",
            value="adopt",
            # NOTE: could include description as tooltip in label
            # label='<div data-tooltip="This is a tooltip">Hover me</div>'
            # help="If and how agents update their risk attitude",
        ),
        "risk_distribution": mo.ui.dropdown(
            value="uniform",
            options=HawkDoveMultipleRiskModel.risk_distribution_options,
            label="Risk distribution",
            # "description": "Distribution for initial risk attitudes",
        ),
        "include_endpoints": mo.ui.checkbox(
            value=True,
            label="Include risk attitudes 0 and 9",
            # label='<div data-tooltip="This is a tooltip">Hover over me</div>'
        ),
        "adjust_every": mo.ui.slider(
            start=1,
            stop=30,
            step=1,
            value=10,
            label="Adjustment frequency (# rounds)",
            show_value=True,
            # "description": "How many rounds between risk adjustment",
        ),
        "adjust_neighborhood": mo.ui.dropdown(
            options=neighborhood_sizes,
            label="Adjustment neighborhood size",
            value=default_neighborhood_size,
        ),
        "adjust_payoff": mo.ui.dropdown(
            label="Adjustment comparison period",
            value="recent",
            options=HawkDoveMultipleRiskModel.supported_adjust_payoffs,
            # "description": "Compare recent payoff (since last adjustment "
            # + "round) or total (cumulative from start) when adjusting risk attitudes",
        ),
    }
)
