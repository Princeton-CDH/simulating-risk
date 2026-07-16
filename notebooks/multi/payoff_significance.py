import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    from simulatingrisk.doc_utils import docs_header

    docs_header()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hawk/Dove with Multiple Risk-Attitudes : Payoff Significance

    The payoff analysis shows that the median and quartiles are lower for Risk-Moderates than for other Risk-Attitudes. Is that signficant? How confident are we in these numbers?

    **tl;dr**: Confidence intervals based on bootstrap sampling (calculated two different ways) are very small. We are highly confident in these numbers.
    """)
    return


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt
    import seaborn as sns
    import matplotlib.pyplot as plt

    from utils import load_agent_data

    data_dir = Path("data/no_adjustment/")
    return alt, data_dir, load_agent_data, mo, pl, plt, sns


@app.cell
def _(data_dir, load_agent_data, pl):
    model_agent_df = (
        pl.concat(load_agent_data(data_dir))
        .with_columns(
            # calculate a scaled points value so we can compare across runs with different length and play neighborhood
            scaled_points=pl.col("points")
            .truediv(pl.col("play_neighborhood"))
            .truediv(pl.col("Step"))
            .mul(100)
        )
        .collect()
    )
    return (model_agent_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
 
    """)
    return


@app.cell
def _(mo, model_agent_df, sample_size):
    mo.md(f"""
    The full set of agent data is too large to process easily, so we test a sample for significance.

    - {model_agent_df.height:,} total rows 
    - sample size: {sample_size:,}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The Seaborn plotting library has built-in support for [bootstrap sampling for confidence intervals](https://seaborn.pydata.org/tutorial/error_bars.html#confidence-interval-error-bars), so first we try that on our sample.

    The line chart with horizontal error bars is the based on the mean of the cumulative payoff distribution. The bootstrap sampling results in confidence interval bars that are very close to our data points.  (Smaller samples resulted in slightly wider confidence intervals.)

    We pair that with a jitter plot to show the ranges of the distribution another way.
    """)
    return


@app.cell
def _(model_agent_df, plt, sns):

    # sample_size = 200_000
    # sample_size = 10_000   # completes in ~660ms
    # sample_size = 20_000  # 809ms
    # sample_size = 300_000  # 8.82s
    sample_size = 1_000_000  # 14.85s

    sample_agents_df = model_agent_df.sample(sample_size)

    f, axs = plt.subplots(2, figsize=(12, 6), sharex=True, layout="tight")
    fig1 = sns.pointplot(
        y=sample_agents_df["scaled_points"],
        x=sample_agents_df["risk_attitude"],
        errorbar="ci",
        capsize=0.3,
        ax=axs[0],
    )
    fig1.set_ylabel("Mean Cumulative Payoff")
    fig1.set_title("Cumulative Payoff Distribution by Risk Attitude")
    fig2 = sns.stripplot(
        y=sample_agents_df["scaled_points"],
        x=sample_agents_df["risk_attitude"],
        jitter=0.3,
        ax=axs[1],
    )
    fig2.set_xlabel("Risk Attitude")
    fig2.set_ylabel("Cumulative Payoff")

    ci_jitter_meanplot = f.get_figure()
    ci_jitter_meanplot.text(
        x=0.5,
        y=1.025,
        s="With 95% confidence intervals based on mean",
        horizontalalignment="center",
    )

    # uncomment to save as a static image
    # ci_jitter_meanplot.savefig("ci_jitter_mean_cumulative_payoff.png")
    return sample_agents_df, sample_size


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A violin plot gives us a differnt way to see the shape of cumulative payoff distributions. (Again run on the sample.)
    """)
    return


@app.cell
def _(plt, sample_agents_df, sns):
    fig_v, ax_v = plt.subplots(figsize=(12, 4))
    vplot = sns.violinplot(
        ax=ax_v, data=sample_agents_df, x="risk_attitude", y="scaled_points"
    )

    vplot.set_xlabel("Risk Attitude")
    vplot.set_ylabel("Cumulative Payoff")
    vplot.set_title("Cumulative Payoff Distribution by Risk Attitude")

    # save to file
    # vplot_fig = vplot.get_figure()
    # vplot_fig.savefig("cumulative_payoff_violinplot.png")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Manual bootstrap sampling

    As a comparison to the Seaborn plots, we implemented our own bootstrap sampling in polars and gather mean, median, and Q1/Q3.  Even for a smaller subset of the data, this is computationally intensive and slow, so the samples were generated and collected separately in a script in this directory.
    """)
    return


@app.cell
def _(model_agent_df, pl):
    payoff_stats_df = model_agent_df.group_by("risk_attitude").agg(
        mean=pl.col.scaled_points.mean(),
        median=pl.col.scaled_points.median(),
        q1=pl.col.scaled_points.quantile(0.25),
        q3=pl.col.scaled_points.quantile(0.75),
    )

    payoff_stats_df
    return (payoff_stats_df,)


@app.cell
def _(data_dir, pl):
    # load pre-calculated bootstrap sampled stats
    bootstrap_stats_df = pl.read_csv(data_dir / "payoff_bootstrap_stats_2pct_10k.csv")
    return (bootstrap_stats_df,)


@app.cell
def _(bootstrap_stats_df):
    bootstrap_stats_df.height
    return


@app.cell
def _(alt, bootstrap_stats_df, pl):
    alt.data_transformers.enable("vegafusion")

    r4_bins = (
        alt.Chart(bootstrap_stats_df.filter(pl.col.risk_attitude.eq(4)))
        .mark_bar()
        .encode(
            alt.X("mean:Q", bin=True),
            y="count()",
        )
    )

    r4_bins
    return


@app.cell
def _(bootstrap_stats_df, pl):
    # calculate 95% confidence interval for each risk attitude

    sample_ci_bounds = bootstrap_stats_df.group_by("risk_attitude").agg(
        # 95% confidence interval for mean
        mean_ci_lower=pl.col.mean.quantile(0.025),
        mean_ci_upper=pl.col.mean.quantile(0.975),
        # 95% confidence interval for median
        median_ci_lower=pl.col.median.quantile(0.025),
        median_ci_upper=pl.col.median.quantile(0.975),
        # q1 confidence interval
        q1_ci_lower=pl.col.q1.quantile(0.025),
        q1_ci_upper=pl.col.q1.quantile(0.975),
        # q3 confidence interval
        q3_ci_lower=pl.col.q3.quantile(0.025),
        q3_ci_upper=pl.col.q3.quantile(0.975),
    )

    sample_ci_bounds.sort("risk_attitude")
    return (sample_ci_bounds,)


@app.cell
def _(alt, bootstrap_stats_df, pl, sample_ci_bounds):
    # graph results for risk attitude 4 to check the logic
    # based on https://inferentialthinking.com/chapters/13/2/bootstrap/

    mean_r4_bin_chart = (
        alt.Chart(bootstrap_stats_df.filter(pl.col.risk_attitude.eq(4)))
        .mark_bar()
        .encode(
            alt.X("mean:Q", bin=True),
            y="count()",
        )
    )
    mean_r4_rule_chart = (
        alt.Chart(sample_ci_bounds.filter(pl.col.risk_attitude.eq(4)))
        .mark_rule(color="yellow", size=5)
        .encode(
            x="mean_ci_lower",
            x2="mean_ci_upper",
            y=alt.value("height"),
            # y='count()',
        )
    )

    (mean_r4_bin_chart + mean_r4_rule_chart)
    return


@app.cell
def _(alt, payoff_stats_df, sample_ci_bounds):
    ci_bars = (
        alt.Chart(sample_ci_bounds)
        .mark_rule(color="yellow", size=15, opacity=1.0)
        .encode(
            y="mean_ci_lower",
            y2="mean_ci_upper",
            x="risk_attitude",
        )
    )

    stats_base_chart = alt.Chart(payoff_stats_df)
    mean_points = stats_base_chart.mark_point(size=30).encode(
        y=alt.Y("mean").scale(zero=False), x="risk_attitude"
    )

    mean_line = stats_base_chart.mark_line().encode(
        y=alt.Y("mean").scale(zero=False), x="risk_attitude"
    )

    ci_bars + mean_points + mean_line
    return


@app.cell
def _(alt, payoff_stats_df, sample_ci_bounds):
    # write a method to create the combined line + points chart with confidence interval

    def chart_stat_ci(measure):
        # assumes sample_ci_bounds and payoff_stats_df are already set up

        # draw rulers for 95% confidence interval
        ci_bars = (
            alt.Chart(sample_ci_bounds)
            .mark_rule(color="yellow", size=15)
            .encode(
                y=f"{measure}_ci_lower",
                y2=f"{measure}_ci_upper",
                x="risk_attitude",
            )
        )
        stats_base_chart = alt.Chart(payoff_stats_df)
        points = stats_base_chart.mark_point(size=10).encode(
            y=alt.Y(measure, title=f"{measure.title()}").scale(zero=False),
            x=alt.X("risk_attitude", title="Risk Attitude"),
        )
        line = stats_base_chart.mark_line().encode(
            y=alt.Y(measure).scale(zero=False), x="risk_attitude"
        )

        return points + line + ci_bars

    return (chart_stat_ci,)


@app.cell
def _(chart_stat_ci):
    (
        chart_stat_ci("mean")
        | chart_stat_ci("median")
        | chart_stat_ci("q1")
        | chart_stat_ci("q3")
    ).properties(
        title="Statistics for cumulative payoff distribution with confidence intervals"
    )
    return


if __name__ == "__main__":
    app.run()
