import marimo

__generated_with = "0.23.11"
app = marimo.App(
    width="medium",
    app_title="Overview - Hawk/Dove with Multiple Risk-Attitudes",
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
    # Hawk/Dove with Multiple Risk-Attitudes in a Population

    Overview of simulation batch run data. Includes information about parameters and number of runs, with brief analysis of run length and convergence correlation with initial parameters.
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt
    import seaborn as sns

    from simulatingrisk.hawkdovemulti.batch_run import params

    data_dir = Path("data/no_adjustment/")
    return alt, data_dir, mo, params, pl, sns


@app.cell
def _(df, mo, params, pl, run_groups_df, runs_per_group, total_agent_rows):

    param_opts = []

    for key, value in params["no_adjustment"].items():
        if isinstance(value, (list, tuple)):
            value_str = ", ".join([str(v) for v in value])
        else:
            value_str = str(value)
        param_opts.append(f"- **{key}**: {value_str}")

    param_info = "\n".join(param_opts)

    # aggregate by status for plotting and reporting
    status_df = df.group_by("status").agg(count=pl.len(), percent=pl.len() / df.height)
    # export total and percent of runs that converged for inclusion in text
    converged_stats = status_df.filter(pl.col.status.eq("converged")).to_dicts()[0]

    # TODO: would be great to report how many runs per parameter combination (hopefully 100)
    overview_txt = f"""
    Analyzing data from **{df.height:,}** total simulation runs.  Data was collected for model and agents at the last round only.

    **{converged_stats["count"]:,} ({converged_stats["percent"] * 100:.1f}%)**  simulations converged.

    Simulations were run on the following combination of initial parameters:
    {param_info}

    This resulted in **{run_groups_df.height:,}** combinations; each set of parameters was run **{runs_per_group:,} times**.

    Agent data for those simualations results in **{total_agent_rows:,}** rows.
    """
    mo.md(overview_txt)
    return (status_df,)


@app.cell
def _(data_dir, pl):
    # load all model files in the no_adjustment data directory
    df = pl.scan_csv(
        [str(file) for file in data_dir.glob("*_model.csv") if file.stat().st_size != 0]
    ).collect()
    return (df,)


@app.cell
def _(alt, mo, pl, status_df):
    # generate a nice string version of the % for display
    _status_pct_df = status_df.with_columns(
        percent_str=pl.col.percent.map_elements(
            lambda x: f"{x * 100:,.2f}%", return_dtype=pl.String
        )
    )

    _count_bar = (
        alt.Chart(_status_pct_df)
        .mark_bar()
        .encode(y="status", x="count", color="status")
    )

    text_color = "white" if mo.app_meta().theme == "light" else "black"
    _percent_text = _count_bar.mark_text(xOffset=20).encode(
        y=alt.Y("status", title=""),
        x=alt.X("count", title="Number of Simulations"),
        text="percent_str",
        color=alt.value(text_color),
    )

    mo.ui.altair_chart((_count_bar + _percent_text).properties(width=550))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To check if convergence is correlated with any of the initial parameters, we generate and graph a correlation matrix.
    """)
    return


@app.cell
def _(df, pl):
    # we want to know if there is any correlation between convergence / run length and the starting parameters

    corr_matrix_df = (
        # add a boolean column for status converged
        df.with_columns(converged=pl.col.status.eq("converged"))
        .rename({"Step": "run length"})
        .select(
            "run length",
            "grid_size",
            "play_neighborhood",
            "observed_neighborhood",
            "hawk_odds",
            "random_play_odds",
            "converged",
            "include_endpoints",
        )
        .corr()
    )

    # uncomment to display
    # corr_matrix_df
    return (corr_matrix_df,)


@app.cell
def _(alt, corr_matrix_df, pl):
    # add labels and unpivot for graphing as a heatmap

    # add columns as label, then unpivot to long form for charting
    corr_matrix_long_df = (
        corr_matrix_df.with_columns(pl.Series("var_x", corr_matrix_df.columns))
        .unpivot(
            on=corr_matrix_df.columns,
            index="var_x",
            variable_name="var_y",
            value_name="correlation",
        )
        .filter(pl.col.var_y.is_in(["run length", "converged"]))
        .filter(~pl.col.var_x.is_in(["run length", "converged"]))
        .with_columns(
            correlation_str=pl.col.correlation.map_elements(
                lambda x: f"{x:,.2f}", return_dtype=pl.String
            )
        )
    )

    _heatmap_corr_chart = (
        alt.Chart(corr_matrix_long_df)
        .mark_rect()
        .encode(
            x=alt.X(
                "var_x:O",
                title="",
                axis=alt.Axis(
                    orient="top",  # move axis to top
                    labelAngle=-45,  # angle the labels (negative = counterclockwise)
                ),
            ),
            y=alt.Y("var_y:O", title=""),
            # use spectral theme since we have both negative and positive correlations
            color=alt.Color("correlation").scale(scheme="spectral"),
        )
        .properties(width=450, height=300)
    )

    _text_corr_chart = _heatmap_corr_chart.mark_text().encode(
        x="var_x:O",
        y="var_y:O",
        text="correlation_str",
        # for contrast, vary the color based on the intensity of the correlation, negative or positive
        color=alt.condition(
            "abs(datum.correlation) > 0.3", alt.value("white"), alt.value("black")
        ),
    )

    _heatmap_corr_chart + _text_corr_chart
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    There is a noticeable correlation between grid size and convergence / simulation run length.  Convergence is slightly correlated with grid size; run length is negatively correlated with grid size.  This is because the samll 5x5 simulation has a much lower convergence rate, with a corresponding number of simulations that ran until the batch-run configured maximum of 300 steps.

    A bar chart of simulation run length (based on last step) faceted by grid size shows that the majority of runs end fairly quickly.
    """)
    return


@app.cell
def _(alt, df, mo, pl):
    # generate aggregate counts by step for graphing (charting the full data without aggregation is too large for altair)
    grid_runlength_df = df.group_by("Step", "status", "grid_size").agg(count=pl.len())

    mo.ui.altair_chart(
        alt.Chart(grid_runlength_df)
        .mark_bar()
        .encode(
            x=alt.X("Step"),
            y=alt.Y("count", title="Number of Simulations"),
            tooltip="count",
            color="status",
        )
        .properties(width=205, height=180, title="Simulation run length")
        .facet("grid_size", title="Simulation run length by grid size")
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A "boxenplot" is a helpful way to see the distribution of simulation run lengths over grid sizes.
    """)
    return


@app.cell
def _(df, sns):
    sns.boxenplot(data=df, y="Step", x="grid_size")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The other parameter with a noticeable impact on convergence is the random play odds - an increase in random play odds results in a decrease in convergence and an increase in run length.
    """)
    return


@app.cell
def _(df, sns):
    sns.boxenplot(data=df, y="Step", x="random_play_odds")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Data file review

    List and checks on the files, parameters, and number of runs included in the data used for analysis.


    ### Model data
    """)
    return


@app.cell
def _(data_dir, mo, pl):
    # create a dataframe with overview information the files we're drawing from,
    # to confirm that the files have the data and parameters we expect

    def get_data_file_info(file_iter):
        file_info = []
        for data_file in file_iter:
            file_size = data_file.stat().st_size
            rows = None
            max_step = None
            cols = None
            n_cols = None
            if file_size:
                file_df = pl.read_csv(data_file)
                rows = file_df.height
                if "Step" in file_df.columns:
                    max_step = file_df["Step"].max()
                else:
                    print(f"data but no step in {data_file.name}")
                cols = file_df.columns
                n_cols = len(cols)
            file_info.append(
                {
                    "file_name": data_file.name,
                    "file_size": file_size,
                    "rows": rows,
                    "max_step": max_step,
                    # "columns": cols,
                    "n_cols": n_cols,
                }
            )
        file_info_df = pl.from_dicts(file_info)
        return file_info_df

    model_file_info_df = get_data_file_info(data_dir.glob("*_model.csv"))
    # check that there is a corresponding agent data file
    model_file_info_df = model_file_info_df.with_columns(
        agent_file_name=pl.col.file_name.str.replace("_model", "_agent")
    ).with_columns(
        agent_file_exists=pl.col.agent_file_name.map_elements(
            lambda x: (data_dir / x).exists()
        )
    )

    mo.ui.table(model_file_info_df, page_size=15, selection=None)
    return get_data_file_info, model_file_info_df


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Check that the data doesn't include any incomplete or unexpected data.
    """)
    return


@app.cell
def _(model_file_info_df, pl):
    # we expect the same number of parameters in each file (may be redundant; can't load into common dataframe if they don't match)
    assert (model_file_info_df["n_cols"].n_unique()) == 1, (
        "All files should have the same number of parameters"
    )

    # less than 3240 means incomplete run (not all parameter combos)
    assert model_file_info_df.filter(pl.col.rows.lt(3240)).height == 0, (
        "Data should not include files with less than 3240 rows (incomplete run)"
    )

    # max step 300 was used for the full set fo 100 batches
    assert model_file_info_df.filter(pl.col.max_step.ne(300)).height == 0, (
        "Data should only include files with max step of 300"
    )

    # all model files should have agent  data
    assert model_file_info_df.filter(pl.col.agent_file_exists.eq(False)).height == 0, (
        "All model data files should have corresponding agent data file"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Aggregate collected data by the initial parameters and check combination of parameters and number of runs per parameter set.
    """)
    return


@app.cell
def _(df, params, pl):
    # runs per parameter combination
    run_groups_df = df.group_by(params["no_adjustment"].keys()).agg(runs=pl.len())

    # we expect the same number of runs for each parameter set
    assert (run_groups_df["runs"].n_unique()) == 1

    runs_per_group = run_groups_df["runs"].max()

    run_groups_df
    return run_groups_df, runs_per_group


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Agent data
    """)
    return


@app.cell
def _(data_dir, get_data_file_info, mo, pl):

    agent_file_info_df = get_data_file_info(data_dir.glob("*_agent.csv"))
    # check that there is a corresponding model file
    agent_file_info_df = agent_file_info_df.with_columns(
        model_file_name=pl.col.file_name.str.replace("_agent", "_model")
    ).with_columns(
        model_file_exists=pl.col.model_file_name.map_elements(
            lambda x: (data_dir / x).exists()
        )
    )

    mo.ui.table(agent_file_info_df, page_size=15, selection=None)
    return (agent_file_info_df,)


@app.cell
def _(agent_file_info_df):
    total_agent_rows = agent_file_info_df["rows"].sum()
    total_agent_rows
    return (total_agent_rows,)


@app.cell
def _(agent_file_info_df, pl):
    # we expect the same number of parameters in each file
    assert (agent_file_info_df["n_cols"].n_unique()) == 1, (
        "All files should have the same number of parameters"
    )

    # max step 300 was used for the full set fo 100 batches
    assert agent_file_info_df.filter(pl.col.max_step.ne(300)).height == 0, (
        "Data should only include files with max step of 300"
    )

    # all agent files should have model data
    assert agent_file_info_df.filter(pl.col.model_file_exists.eq(False)).height == 0, (
        "All agent data files should have corresponding model data file"
    )
    return


if __name__ == "__main__":
    app.run()
