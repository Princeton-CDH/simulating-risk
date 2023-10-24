# solara/jupyterviz app
import altair as alt
from mesa.experimental import JupyterViz
import solara


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


def agents_by_risk(model):
    """plot total number of agents for each risk attitude"""
    agent_df = model.datacollector.get_agent_vars_dataframe().reset_index().dropna()
    if agent_df.empty:
        return

    last_step = agent_df.Step.max()
    # plot current status / last round
    last_round = agent_df[agent_df.Step == last_step]
    # count number of agents for each status
    grouped = last_round.groupby("risk_level", as_index=False).agg(
        total=("AgentID", "count")
    )

    # draw a bar chart to indicate the number of agents for each
    # risk attitude
    # configure domain to always display all statuses
    # TODO: limit to 4 when not including diagonals
    # (fixme: include diagonal checkbox param not working?)
    bar_chart = (
        alt.Chart(grouped)
        .mark_bar(width=10)
        .encode(
            x=alt.X(
                "risk_level",
                title="risk attitude",
                scale=alt.Scale(domain=[0, 8]),
            ),
            y=alt.Y("total", title="Number of agents"),
        )
    )
    return solara.FigureAltair(bar_chart)


def hawks_by_risk(model):
    """plot rolling mean of percent of agents in each risk attitude
    who chose hawk over last several rounds"""

    agent_df = model.datacollector.get_agent_vars_dataframe().reset_index().dropna()
    if agent_df.empty:
        return

    last_step = agent_df.Step.max()
    # limit to last N rounds (how many ?)
    last_n_rounds = agent_df[agent_df.Step.gt(last_step - 60)].copy()
    last_n_rounds["hawk"] = last_n_rounds.choice.apply(
        lambda x: 1 if x == "hawk" else 0
    )
    # for each step and risk level, get number of agents and number of hawks
    grouped = (
        last_n_rounds.groupby(["Step", "risk_level"], as_index=False)
        .agg(hawk=("hawk", "sum"), agents=("AgentID", "count"))
        .sort_values("Step")
    )
    # calculate percent hawk within each group
    grouped["percent_hawk"] = grouped.apply(lambda row: row.hawk / row.agents, axis=1)
    # now calculate rolling percent within each risk attitude
    # thanks to https://stackoverflow.com/a/53339204
    grouped["rolling_pct_hawk"] = grouped.groupby("risk_level")[
        "percent_hawk"
    ].transform(lambda x: x.rolling(15, 1).mean())

    # starting domain 0-50 so it doesn't jump / expand as much
    max_step = max(last_step or 0, 50)
    min_step = max(max_step - 50, 0)

    chart = (
        alt.Chart(grouped[grouped.Step.gt(min_step - 1)])
        .mark_line()
        .encode(
            x=alt.X("Step", scale=alt.Scale(domain=[min_step, max_step])),
            y=alt.Y(
                "rolling_pct_hawk",
                title="rolling % hawk",
                scale=alt.Scale(domain=[0, 1]),
            ),
            color=alt.Color("risk_level:N"),
        )
    )
    return solara.FigureAltair(chart)


page = JupyterViz(
    HawkDoveVariableRiskModel,
    jupyterviz_params_var,
    measures=[plot_hawks, agents_by_risk, hawks_by_risk],
    name="Hawk/Dove game with variable risk attitudes",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)
# required to render the visualization with Jupyter/Solara
page
