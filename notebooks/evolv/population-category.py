import marimo

__generated_with = "0.23.11"
app = marimo.App(
    width="medium",
    app_title="Population Categories - Hawk/Dove with Evolving Risk-Attitudes",
    html_head_file="../docs_head.html",
)


@app.cell(hide_code=True)
def _():
    from simulatingrisk.doc_utils import docs_header

    docs_header()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Population Categories - Hawk/Dove with Evolving Risk-Attitudes

    In this simulation, agents periodically adjusted to adopt the most successful risk-attitude in their adjustment neighborhood. The simulation converges when those adjustments have stabilized and the number of agents still adjusting is zero or a small proportion of the population.

    To provide a high-level view of the population, we define a set of population category based on the primary and secondary majority of risk-attitudes for agents in the stabilized simulation.  This notebook provides analysis of the final population category at convergence across all batch runs.
    """)
    return


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import polars as pl

    from simulatingrisk.hawkdovemulti import analysis_utils

    data_dir = Path("data/default/")
    return alt, analysis_utils, data_dir, mo, pl


@app.cell
def _(data_dir, pl):
    df = pl.scan_csv([str(file) for file in data_dir.glob("*_model.csv")]).collect()
    return (df,)


@app.cell
def _(df):
    status_by_dist = (
        df.group_by("risk_distribution", "status").len().rename({"len": "count"})
    )
    return (status_by_dist,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We know from other analysis that the initial risk distribution has a significant impact on the resulting risk attitudes, but that it does not significantly impact rates of convergence.
    """)
    return


@app.cell
def _(alt, status_by_dist):
    alt.Chart(status_by_dist).mark_bar().encode(
        x="risk_distribution:N", y="count", color="status:N"
    ).properties(
        title="Simulation end state by risk distribution",
        width=250,
        height=400,
    )
    return


@app.cell
def _(df):
    # filter and restrict further analysis to runs that converged
    converged_df = df.filter(status="converged")
    return (converged_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Here is a chart of the number of simulations ending in each population category, for all simulations that started with an initial uniform distribution of risk attitudes.
    """)
    return


@app.cell
def _(analysis_utils, converged_df):
    # output just the uniform distribution chart by itself, for inclusion in the paper

    uniform_riskdist_population_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(
            converged_df.filter(risk_distribution="uniform")
        )
    )

    uniform_riskdist_population_chart.properties(
        title="Distribution of Convergence States across Simulation Runs"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To see which parameters impact the final population, we graph population categories for simulations segmented by various parmeters.

    ---

    ### Initial Risk-Attitude distribution
    """)
    return


@app.cell
def _(alt, analysis_utils, converged_df):
    analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(
            converged_df, "risk_distribution"
        )
    ).facet("risk_distribution", columns=3).properties(
        title=alt.TitleParams(
            "Distribution of Convergence States by Initial Risk Attitude Distribution",
            anchor="middle",
        )
    ).resolve_scale(y="shared").configure_legend(
        orient="none", legendX=750, legendY=400
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Grid Size
    """)
    return


@app.cell
def _(alt, analysis_utils, converged_df):

    gridsize_opulation_category_chart = (
        analysis_utils.graph_population_risk_category(
            analysis_utils.groupby_population_risk_category(converged_df, "grid_size")
        )
        .facet("grid_size")
        .properties(
            title=alt.TitleParams("Distribution of Convergence States by Grid Size")
        )
    )
    gridsize_opulation_category_chart
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Random play odds

    Likelihood on any given turn that an agent will choose play randomly.
    """)
    return


@app.cell
def _(alt, analysis_utils, converged_df):

    analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(
            converged_df, "random_play_odds"
        )
    ).facet("random_play_odds").properties(
        title=alt.TitleParams(
            "Distribution of Convergence States by Odds of Random Play"
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Initial Hawk Odds

    Odds that agents play hawk on the first turn, when they do not yet have any information about their neighbors.
    """)
    return


@app.cell
def _(alt, analysis_utils, converged_df):

    analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(converged_df, "hawk_odds")
    ).facet("hawk_odds").properties(
        title=alt.TitleParams(
            "Distribution of Convergence States over odds of playing Hawk on the first round"
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### With and without extreme risk attitudes

    Simulations were run with and without extreme risk-attitudes, which are the end points of our range of risk attitudes.
    - 0 : always hawk
    - 9 : always dove
    """)
    return


@app.cell
def _(alt, analysis_utils, converged_df):
    analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(
            converged_df, "include_endpoints"
        )
    ).facet("include_endpoints").properties(
        title=alt.TitleParams(
            "Distribution of Convergence States with and without extreme risk-attitudes"
        )
    )
    return


if __name__ == "__main__":
    app.run()
