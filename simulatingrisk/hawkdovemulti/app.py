# solara/jupyterviz app
import altair as alt
from mesa.experimental import JupyterViz
import solara


from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel
from simulatingrisk.hawkdove.server import (
    agent_portrayal,
    common_jupyterviz_params,
    draw_hawkdove_agent_space,
    neighborhood_sizes,
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
        "adjust_neighborhood": {
            "type": "Select",
            "value": 8,
            "values": neighborhood_sizes,
            "label": "Adjustment neighborhood size",
        },
    }
)


def plot_agents_by_risk(model):
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

    # bar chart to show number of agents for each risk attitude
    # configure domain to always display all statuses;
    # limit changes depending on if diagonals are included
    # (NOTE: bug in mesa 2.12, checkbox param does not propagate)
    bar_chart = (
        alt.Chart(grouped)
        .mark_bar(width=15)
        .encode(
            x=alt.X(
                "risk_level",
                title="risk attitude",
                # don't display any 0.5 ticks when max is 4
                axis=alt.Axis(tickCount=model.play_neighborhood + 1),
                scale=alt.Scale(domain=[0, model.play_neighborhood]),
            ),
            y=alt.Y("total", title="Number of agents"),
        )
    )
    return solara.FigureAltair(bar_chart)


def plot_hawks_by_risk(model):
    """plot rolling mean of percent of agents in each risk attitude
    who chose hawk over last several rounds"""

    # in the first round, mesa returns a dataframe full of NAs; ignore that
    agent_df = (
        model.datacollector.get_agent_vars_dataframe()
        .reset_index()
        .dropna(subset=["AgentID"])
    )
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
    HawkDoveMultipleRiskModel,
    jupyterviz_params_var,
    measures=[plot_hawks, plot_agents_by_risk, plot_hawks_by_risk],
    name="Hawk/Dove game with multiple risk attitudes",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)
# required to render the visualization with Jupyter/Solara
page
