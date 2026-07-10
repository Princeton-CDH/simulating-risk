import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hawk/Dove with Multiple Risk-Attitudes in a Population

    Overview of simulation batch run data.
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt

    from simulatingrisk.hawkdovemulti.batch_run import params

    data_dir = Path("data/no_adjustment/")
    return alt, data_dir, mo, params, pl


@app.cell
def _(df, mo, params):

    param_opts = []

    for key, value in params["no_adjustment"].items():
        if isinstance(value, (list, tuple)):
            value_str = ", ".join([str(v) for v in value])
        else:
            value_str = str(value)
        param_opts.append(f"- **{key}**: {value_str}")

    param_info = "\n".join(param_opts)

    # TODO: would be great to report how many runs per parameter combination (hopefully 100)
    overview_txt = f"""
    Data from **{df.height:,}** total simulation runs.

    Based on the following combination of starting parameters:
    {param_info}
    """
    mo.md(overview_txt)
    return


@app.cell
def _(data_dir, pl):
    # df = pl.scan_csv([str(file) for file in data_dir.glob("*_model.csv")]).collect()
    # TODO: when we aggregate, need to add a field to make run ids and iterations unique across all files

    # df = pl.read_csv("data/no_adjustment/2026-07-08T164725_967961_model.csv")

    # df = pl.read_csv("data/no_adjustment/job_task_2026-07-08T165813_431344_model.csv")

    df = pl.scan_csv(
        [
            str(file)
            for file in data_dir.glob("2026-07-09*_model.csv")
            if file.stat().st_size != 0
        ]
    ).collect()
    return (df,)


@app.cell
def _(alt, df, pl):

    alt.Chart(df.filter(pl.col.Step.gt(100))).mark_bar().encode(
        y="status", x="count()", color="status"
    ).properties(width=450).facet("grid_size", columns=1)
    return


@app.cell
def _(df):
    df.head()
    return


@app.cell
def _(df, pl):
    # generate aggregate counts by step for graphing (unaggregated the data is too large)
    runlength_df = df.group_by("Step").agg(count=pl.len())
    runlength_df
    return (runlength_df,)


@app.cell
def _(alt, runlength_df):
    alt.Chart(runlength_df).mark_bar().encode(
        x="Step", y=alt.Y("count"), tooltip="count"
    )
    return


@app.cell
def _(alt, runlength_df):

    alt.Chart(runlength_df).mark_bar().encode(
        x="Step", y=alt.Y("count"), tooltip="count"
    ).properties(title="Simulation run length")
    return


@app.cell
def _(df, pl):
    df.group_by("status").agg(
        count=pl.len(), percent=pl.len() / df.height
    )  # value_counts()
    return


@app.cell
def _(alt, runlength_df):
    # todo aggregate differently for facet counts

    alt.Chart(runlength_df).mark_bar().encode(
        x="Step", y=alt.Y("count"), tooltip="count"
    ).facet("grid_size", columns=2)
    return


@app.cell
def _(alt, df, mo):

    mo.ui.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Step", title="Run length"),
            y=alt.Y("count()", title="Number of Runs"),
            color="status",
        )
        .properties(title="Simulation run length")
        .facet("risk_distribution", columns=3)
    )
    return


if __name__ == "__main__":
    app.run()
