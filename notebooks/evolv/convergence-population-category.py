import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell
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
    df
    return (df,)


@app.cell
def _(alt, df, mo):
    mo.ui.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Step", title="Run length"),
            y=alt.Y("count()", title="Number of Runs"),
        )
        .properties(title="Simulation run length")
        .facet("risk_distribution", columns=3)
    )
    return


@app.cell
def _(df):
    status_by_dist = (
        df.group_by("risk_distribution", "status").len().rename({"len": "count"})
    )

    status_by_dist
    return (status_by_dist,)


@app.cell
def _(alt, status_by_dist):
    alt.Chart(status_by_dist).mark_bar().encode(
        x="risk_distribution:N", y="count", color="status:N"
    ).properties(
        title="Simulation status (converged/running) by risk distribution",
        width=250,
        height=400,
    )
    return


@app.cell
def _(df):
    converged_df = df.filter(
        status="converged"
    )  # .group_by("risk_distribution", "Step").agg(count=pl.len())
    converged_df
    return (converged_df,)


@app.cell
def _(converged_df, pl):
    subset = {}
    for distribution in converged_df["risk_distribution"].unique():
        subset[distribution] = converged_df.filter(
            pl.col("risk_distribution") == distribution
        )
    return (subset,)


@app.cell
def _():
    # alt.Chart(converged_df).mark_boxplot(size=20).encode(
    #     x='risk_distribution:N',
    #     y='Step',
    # ).properties(
    #     title=alt.TitleParams(
    #         "Simulation run length by risk distribution",
    #         subtitle="(converged runs only)"),
    #     width=350, height=450)
    return


@app.cell
def _(analysis_utils, subset):

    uniform_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(subset["uniform"])
    ).properties(title="Uniform")

    normal_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(subset["normal"])
    ).properties(title="Normal")

    bimodal_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(subset["bimodal"])
    ).properties(title="Bimodal")

    skewedleft_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(subset["skewed left"])
    ).properties(title="Skewed Left")

    skewedright_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(subset["skewed right"])
    ).properties(title="Skewed Right")
    return (
        bimodal_chart,
        normal_chart,
        skewedleft_chart,
        skewedright_chart,
        uniform_chart,
    )


@app.cell
def _(
    alt,
    bimodal_chart,
    normal_chart,
    skewedleft_chart,
    skewedright_chart,
    uniform_chart,
):
    # display the same charts but in two rows

    (
        (uniform_chart | normal_chart | bimodal_chart)
        & (skewedleft_chart | skewedright_chart)
    ).properties(
        title=alt.TitleParams(
            "Distribution of Convergence States by Initial Risk Attitude Distribution",
            anchor="middle",
        )
    ).resolve_scale(y="shared").configure_legend(
        orient="none", legendX=750, legendY=400
    )
    return


@app.cell
def _(analysis_utils, converged_df):
    analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(
            converged_df, "risk_distribution"
        )
    ).facet("risk_distribution", columns=3).configure_legend(
        orient="none", legendX=750, legendY=400
    )
    return


@app.cell
def _(analysis_utils, converged_df):

    gridsize_opulation_category_chart = analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(converged_df, "grid_size")
    ).facet("grid_size")

    gridsize_opulation_category_chart
    # population_category_chart
    # analysis_utils.groupby_population_risk_category(converged_df, "grid_size")
    return


@app.cell
def _(analysis_utils, converged_df):

    analysis_utils.graph_population_risk_category(
        analysis_utils.groupby_population_risk_category(
            converged_df, "random_play_odds"
        )
    ).facet("random_play_odds")
    return


if __name__ == "__main__":
    app.run()
