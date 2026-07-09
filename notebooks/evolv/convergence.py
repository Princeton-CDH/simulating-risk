import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell
def _():
    # check convergence of simulation runs with evolving risk attitudes
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt

    data_dir = Path("data/default/")
    return alt, data_dir, mo, pl


@app.cell
def _(data_dir, pl):
    # in case we need to report on specific files
    # data_files = [str(file) for file in data_dir.glob("*_model.csv")]
    df = pl.scan_csv([str(file) for file in data_dir.glob("*_model.csv")]).collect()
    df
    return (df,)


@app.cell
def _(df):
    print(f"Analyzing {df.height:,} runs")
    return


@app.cell
def _(df, pl):
    # generate aggregate counts by step for graphing (unaggregated the data is too large)
    runlength_df = df.group_by("Step").agg(count=pl.len(), percent=pl.len() / df.height)
    runlength_df.sort("count", descending=True)
    return (runlength_df,)


@app.cell
def _(alt, runlength_df):
    alt.Chart(runlength_df).mark_bar().encode(
        x="Step", y=alt.Y("count"), tooltip="count"
    ).properties(title="Simulation run length")
    return


@app.cell
def _(df, pl):
    df.group_by("status").agg(count=pl.len(), percent=pl.len() / df.height)
    return


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
def _(alt, df, mo):
    mo.ui.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Step", title="Run length"),
            y=alt.Y("count()", title="Number of Runs"),
        )
        .properties(title="Simulation run length")
        .facet("random_play_odds", columns=3)
    )
    return


@app.cell
def _(df, pl):
    df.group_by("status", "random_play_odds").agg(
        count=pl.len(), percent=pl.len() / df.height
    )
    return


@app.cell
def _(df, pl):
    df.group_by("status", "include_endpoints").agg(
        count=pl.len(), percent=pl.len() / df.height
    )
    return


@app.cell
def _(df, pl):
    df.group_by("status", "hawk_odds").agg(count=pl.len(), percent=pl.len() / df.height)
    return


@app.cell
def _(df):
    # we want to know if there is any correlation between convergence / run length and the starting parameters

    df_corr = (
        df.to_dummies("status")
        .select(
            "Step",
            "grid_size",
            "play_neighborhood",
            "observed_neighborhood",
            "adjust_neighborhood",
            "hawk_odds",
            "random_play_odds",
            "status_converged",
            "status_running",
        )
        .corr()
    )

    # df_corr = df_corr.with_columns(

    # )

    df_corr
    return (df_corr,)


@app.cell
def _(df, pl):
    # spot check pearson vs spearman

    df.to_dummies("status").select(
        gridsize_pearson=pl.corr("Step", "grid_size", method="pearson"),
        gridsize_spearman=pl.corr("Step", "grid_size", method="spearman"),
        play_nhood_pearson=pl.corr("Step", "play_neighborhood", method="pearson"),
        play_nhood_spearman=pl.corr("Step", "play_neighborhood", method="spearman"),
        converged_pearson=pl.corr("Step", "status_converged", method="pearson"),
        converged_spearman=pl.corr("Step", "status_converged", method="spearman"),
        randplay_pearson=pl.corr("Step", "random_play_odds", method="pearson"),
        randplay_spearman=pl.corr("Step", "random_play_odds", method="spearman"),
    )

    # df_spearman_corr = df.to_dummies("status").select("Step", "grid_size", "play_neighborhood", "observed_neighborhood", "adjust_neighborhood", "hawk_odds", "random_play_odds", "status_converged", "status_running").corr(method="spearman")
    return


@app.cell
def _(df_corr, pl):
    # df_corr.unpivot(on=df_corr.columns + ["Step"]) # , index="param")

    cols = df_corr.columns  # ["Step", "grid_size", ...]

    long = df_corr.with_columns(pl.Series("var_x", cols)).unpivot(  # add row labels
        on=cols,
        index="var_x",
        variable_name="var_y",
        value_name="correlation",
    )
    long = long.filter(
        pl.col.var_y.is_in(["Step", "status_converged", "status_running"])
    ).filter(~pl.col.var_x.is_in(["Step", "status_converged", "status_running"]))
    return (long,)


@app.cell
def _(alt, long):

    alt.Chart(long).mark_rect().encode(
        x="var_x:O",
        y="var_y:O",
        color=alt.Color("correlation").scale(scheme="spectral"),
    ).properties(width=450, height=300)
    return


@app.cell
def _(df, pl):
    df.filter(pl.col.Step.gt(300))
    return


@app.cell
def _(alt, df, mo, pl):
    # how many runs over 1k steps?
    # alt.data_transformers.enable("vegafusion")

    long_runs = df.filter(pl.col.Step.gt(300))

    mo.ui.altair_chart(
        alt.Chart(long_runs)
        .mark_boxplot()
        .encode(x="Step", y="grid_size:N", color="status")
    ).properties(width=450).facet("status", columns=1)
    return (long_runs,)


@app.cell
def _(alt, long_runs, mo):

    mo.ui.altair_chart(
        alt.Chart(long_runs).mark_bar().encode(y="status", x="count()", color="status")
    ).properties(width=450).facet("grid_size", columns=1)
    return


@app.cell
def _(df):
    import seaborn as sns

    sns.boxenplot(data=df, y="Step", x="grid_size")
    return (sns,)


@app.cell
def _(df, sns):
    sns.boxenplot(data=df, y="Step", x="grid_size", hue="risk_distribution")
    return


@app.cell
def _(df, sns):
    sns.boxplot(data=df, y="Step", x="grid_size")
    return


if __name__ == "__main__":
    app.run()
