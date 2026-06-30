import altair as alt
import pandas as pd

from simulatingrisk.hawkdove.model import HawkDoveModel


def plot_wealth(model: HawkDoveModel) -> alt.Chart:
    """Histogram plot of agent wealth levels across risk levels;
    for display in interactive simulation."""

    # generate a histogram of points across risk levels
    risk_wealth = [(agent.risk_level, agent.points) for agent in model.schedule.agents]
    df = pd.DataFrame(risk_wealth, columns=["risk_level", "wealth"])

    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y("wealth", title="Cumulative Payoff"),
            x=alt.X("risk_level", title="Risk Attitude"),
        )
    )


def plot_hawks(model: HawkDoveModel) -> alt.Chart | alt.LayerChart:
    """Plot percent of agents who chose hawk over last several rounds;
    for display in interactive simulation."""

    model_df = model.datacollector.get_model_vars_dataframe().reset_index()

    # limit to last N rounds (how many ?)
    last_n_rounds = model_df.tail(50)
    # determine domain of the chart;
    # starting domain 0-50 so it doesn't jump / expand as much
    max_index = max(model_df.last_valid_index() or 0, 50)
    min_index = max(max_index - 50, 0)

    bar_chart = (
        alt.Chart(last_n_rounds)
        .mark_bar(color="orange")
        .encode(
            x=alt.X(
                "index", title="Step", scale=alt.Scale(domain=[min_index, max_index])
            ),
            y=alt.Y(
                "percent_hawk",
                title="Percent who chose hawk",
                scale=alt.Scale(domain=[0, 1]),
            ),
        )
    )
    # graph rolling average as a line over the bar chart,
    # once we have enough rounds
    if model_df.rolling_percent_hawk.any():
        line = (
            alt.Chart(last_n_rounds)
            .mark_line(color="blue")
            .encode(
                x=alt.X("index", title="Step"),
                y=alt.Y(
                    "rolling_percent_hawk",
                    title="Percent Hawk (Rolling Average)",
                    scale=alt.Scale(domain=[0, 1]),
                ),
            )
        )
        # add the rolling average line on top of the bar chart
        bar_chart += line

    return bar_chart
