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
from simulatingrisk.hawkdove.model import divergent_colors_10

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
        "risk_distribution": {
            "type": "Select",
            "value": "uniform",
            "values": HawkDoveMultipleRiskModel.risk_distribution_options,
            "description": "Distribution for initial risk attitudes",
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

# use same divergent color scale across charts
color_scale_opts = {"domain": list(range(10)), "range": divergent_colors_10}


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
                axis=alt.Axis(tickCount=model.max_risk_level + 1),
                scale=alt.Scale(domain=[model.min_risk_level, model.max_risk_level]),
            ),
            y=alt.Y("total", title="Number of agents"),
            # NOTE: could apply divergent color scheme here, but it's actually
            # distracting from the main point of this chart, which is quantitative
            # color=alt.Color("risk_level:N").scale(**color_scale_opts),
        )
        .properties(title="Number of agents with each risk attitude")
    )
    return solara.FigureAltair(bar_chart)


def plot_risklevel_changes(model):
    """plot the number of agents who updated their risk attitude on
    the last adjustment round"""
    model_df = model.datacollector.get_model_vars_dataframe().reset_index()
    if model_df.empty:
        return
    # subset dataframe to only the adjustment rounds
    model_df = model_df[:: model.adjust_round_n]
    if model_df.empty:
        return
    # limit to fields we need
    model_df = model_df[["index", "num_agents_risk_changed", "sum_risk_level_changes"]]
    # rename columns before they become variable labels
    model_df.rename(
        columns={
            "num_agents_risk_changed": "agents",
            "sum_risk_level_changes": "risk attitude totals",
        },
        inplace=True,
    )
    # "melt" to flatten so we can graph as two variables in altair
    melted_df = (
        model_df.melt(id_vars=["index"])
        .dropna()
        .rename(columns={"variable": "category"})
    )

    line_chart = (
        alt.Chart(melted_df)
        .mark_line()
        .encode(
            y=alt.Y(
                "value",
                title="# changes",
                scale=alt.Scale(domain=[0, model.num_agents]),
            ),
            x=alt.X("index"),
            color="category",
        )
        .properties(title="Risk attitude adjustments")
    )

    return solara.FigureAltair(line_chart)


def plot_hawks_by_risk(model):
    """plot rolling mean of percent of agents in each risk level
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
            color=alt.Color("risk_level:N", title="risk attitude").scale(
                **color_scale_opts
            ),
        )
        .properties(title="Rolling average percent hawk by risk level")
    )
    return solara.FigureAltair(chart)


def plot_wealth_by_risklevel(model):
    """plot wealth distribution for each risk level"""
    agent_df = model.datacollector.get_agent_vars_dataframe().reset_index().dropna()
    if agent_df.empty:
        return

    last_step = agent_df.Step.max()
    # plot current status / last round
    last_round = agent_df[agent_df.Step == last_step]

    wealth_chart = (
        alt.Chart(last_round)
        .mark_boxplot(extent="min-max")
        .encode(
            alt.X(
                "risk_level",
                scale=alt.Scale(domain=[model.min_risk_level, model.max_risk_level]),
                title="risk attitude",
            ),
            alt.Y("points", title="wealth").scale(zero=False),
        )
        .properties(title="Cumulative wealth by risk attitude")
    )
    return solara.FigureAltair(wealth_chart)


page = JupyterViz(
    HawkDoveMultipleRiskModel,
    jupyterviz_params_var,
    measures=[
        plot_agents_by_risk,
        plot_hawks_by_risk,
        plot_wealth_by_risklevel,
        plot_risklevel_changes,
        # plot_hawks,
    ],
    name="Hawk/Dove game with multiple risk attitudes",
    agent_portrayal=agent_portrayal,
    space_drawer=draw_hawkdove_agent_space,
)
# required to render the visualization with Jupyter/Solara
page
