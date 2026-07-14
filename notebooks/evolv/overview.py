import marimo

__generated_with = "0.23.11"
app = marimo.App(
    width="medium",
    app_title="Overview - Hawk/Dove with Evolving Risk-Attitudes",
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
    # Hawk/Dove with Evolving Risk-Attitudes

    Overview of simulation batch run data. Includes information about parameters and number of runs, with brief analysis of run length and convergence correlation with initial parameters.
    """)
    return


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt
    import seaborn as sns

    from simulatingrisk.hawkdovemulti.batch_run import params

    data_dir = Path("data/default/")
    return alt, data_dir, mo, params, pl, sns


@app.cell
def _(df, mo, params, pl, run_groups_df, runs_per_group):
    param_opts = []

    for key, value in params["default"].items():
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
    Analyzing data from **{df.height:,}** total simulation runs.

    **{converged_stats["count"]:,} ({converged_stats["percent"] * 100:.1f}%)**  simulations converged.

    Simulations were run on the following combination of initial parameters:
    {param_info}

    This resulted in **{run_groups_df.height:,}** combinations; each set of parameters was run **{runs_per_group:,} times**.
    """

    mo.md(overview_txt)
    return (status_df,)


@app.cell
def _(data_dir, pl):
    # Load all model data in the folder for this set of simulations + parameter batch runs
    df = pl.scan_csv([str(file) for file in data_dir.glob("*_model.csv")]).collect()
    return (df,)


@app.cell
def _(alt, mo, pl, status_df):
    # display chart of number / percent of runs that converged

    # generate a nice string version of the % for display
    _status_pct_df = status_df.with_columns(
        percent_str=pl.col.percent.map_elements(
            lambda x: f"{x * 100:,.1f}%", return_dtype=pl.String
        )
    )

    _count_bar = (
        alt.Chart(_status_pct_df)
        .mark_bar()
        .encode(y="status", x="count", color="status")
    )

    text_color = "white" if mo.app_meta().theme == "light" else "black"
    _percent_text = _count_bar.mark_text(xOffset=17).encode(
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


@app.cell(hide_code=True)
def _(df, params, pl):
    # we want to know if there is any correlation between convergence / run length and the starting parameters

    # parameters to test correlation
    corr_variables = ["converged", "Step"]

    param_variables = [
        param
        for param, val in params["default"].items()
        # risk distribution is categorical and will be split out;
        # ignore any single-value fields, since there is no variance to check
        if param not in ["risk_distribution"] and isinstance(val, list) and len(val) > 1
    ]

    # risk distribution is categorical; convert to one-hot 0/1 for each
    _matrix_df = df.to_dummies("risk_distribution").with_columns(
        converged=pl.col.status.eq("converged")
    )
    param_variables.extend(
        [c for c in _matrix_df.columns if c.startswith("risk_distribution_")]
    )

    corr_matrix_df = _matrix_df.select(*corr_variables, *param_variables).corr()

    # add a label field to the matrix and reorder fields so label is first
    corr_matrix_df = corr_matrix_df.with_columns(
        pl.Series("var_x", corr_matrix_df.columns)
    ).select("var_x", *corr_matrix_df.columns)

    # uncomment to display
    # corr_matrix_df
    return (corr_matrix_df,)


@app.cell(hide_code=True)
def _(alt, corr_matrix_df, pl):
    # unpivot to long format for charting
    corr_matrix_long_df = (
        corr_matrix_df.unpivot(  # add row labels
            on=corr_matrix_df.columns,
            index="var_x",
            variable_name="var_y",
            value_name="correlation",
        )
        .filter(pl.col.var_y.is_in(["Step", "converged"]))
        .filter(~pl.col.var_x.is_in(["Step", "converged"]))
        .with_columns(correlation=pl.col.correlation.cast(pl.Float32))
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
            # set the domain to make it even and more readable
            color=alt.Color("correlation").scale(scheme="spectral", domain=[-0.2, 0.2]),
        )
    )

    _text_corr_chart = _heatmap_corr_chart.mark_text().encode(
        x="var_x:O",
        y="var_y:O",
        text="correlation_str",
        # for contrast, vary the color based on the intensity of the correlation, negative or positive
        color=alt.condition(
            "abs(datum.correlation) > 0.14", alt.value("white"), alt.value("black")
        ),
    )

    (_heatmap_corr_chart + _text_corr_chart).properties(width=600, height=300)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Most of these effects are very slight. The strongest effect is a correlation between adjustment neighborhood size and simulation run length (looking at a larger number of neighbors when adjusting risk-attitude results in longer runs). There is a similar, weaker effect for observed neighborhood size (the number of neighbors an agent looks at before choosing how to play).  There is a slight correlation between grid size and both run length and convergence; the negative correlation means larger grid sizes tend to converge more quickly (shorter run length) and more frequently.
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
        .properties(width=225, height=150, title="Simulation run length")
        .facet("grid_size", title="Simulation run length by grid size")
    )
    return


@app.cell
def _(alt, df, mo, pl):
    # generate aggregate counts by step for graphing (charting the full data without aggregation is too large for altair)
    adjustnhood_runlength_df = df.group_by("Step", "status", "adjust_neighborhood").agg(
        count=pl.len()
    )

    mo.ui.altair_chart(
        alt.Chart(adjustnhood_runlength_df)
        .mark_bar()
        .encode(
            x=alt.X("Step"),
            y=alt.Y("count", title="Number of Simulations"),
            tooltip="count",
            color="status",
        )
        .properties(width=205, height=150, title="Simulation run length")
        .facet(
            "adjust_neighborhood",
            title="Simulation run length by adjustment neighborhood size",
        )
    )
    return


@app.cell
def _(df, pl):
    # spot check pearson vs spearman

    df.with_columns(converged=pl.col.status.eq("converged")).select(
        gridsize_pearson=pl.corr("Step", "grid_size", method="pearson"),
        gridsize_spearman=pl.corr("Step", "grid_size", method="spearman"),
        play_nhood_pearson=pl.corr("Step", "play_neighborhood", method="pearson"),
        play_nhood_spearman=pl.corr("Step", "play_neighborhood", method="spearman"),
        converged_pearson=pl.corr("Step", "converged", method="pearson"),
        randplay_pearson=pl.corr("Step", "random_play_odds", method="pearson"),
        randplay_spearman=pl.corr("Step", "random_play_odds", method="spearman"),
    )

    # df_spearman_corr = df.to_dummies("status").select("Step", "grid_size", "play_neighborhood", "observed_neighborhood", "adjust_neighborhood", "hawk_odds", "random_play_odds", "status_converged", "status_running").corr(method="spearman")
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


@app.cell
def _(df, sns):
    sns.boxenplot(data=df, y="Step", x="adjust_neighborhood")
    # need to filter the data so we have all same max length
    return


@app.cell
def _(df, sns):
    sns.boxenplot(data=df, y="Step", x="observed_neighborhood")
    return


@app.cell
def _(df, sns):
    ax = sns.boxenplot(data=df, y="Step", x="grid_size", hue="risk_distribution")
    # move legend
    ax.legend(
        bbox_to_anchor=(1.01, 1),  # just outside right edge, top-aligned
        loc="upper left",
        borderaxespad=0,
        title="Risk Distribution",
    )
    # plt.tight_layout()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## Data file review

    List and checks on the files, parameters, and number of runs included in the data used for analysis.
    """)
    return


@app.cell
def _(data_dir, mo, pl):
    # create a dataframe with overview information the files we're drawing from,
    # to confirm that the files have the data and parameters we expect

    def get_data_file_info(file_iter):
        # NOTE: method copied from multi/overview notebook
        file_info = []
        for data_file in file_iter:
            file_size = data_file.stat().st_size
            rows = None
            max_step = None
            cols = None
            n_cols = None
            if file_size:
                file_df = pl.read_csv(data_file)

                # earlier batch runs had different set of grid sizes;
                # used this check to identify, then moved them into testing subfolder
                grid_size_values = file_df["grid_size"].unique().to_list()
                if grid_size_values != [10, 25, 50]:
                    print(
                        f"{data_file} does not have expected grid sizes (has {grid_size_values})"
                    )

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

    file_info_df = get_data_file_info(data_dir.glob("*_model.csv"))

    mo.ui.table(file_info_df, page_size=15, selection=None)
    return (file_info_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Check that the data doesn't include any incomplete or unexpected data.
    """)
    return


@app.cell
def _(file_info_df, pl):
    # we expect the same number of parameters in each file (may be redundant; can't load into common dataframe if they don't match)
    assert (file_info_df["n_cols"].n_unique()) == 1, (
        "All files should have the same number of parameters"
    )

    # less than 14580 means incomplete run (not all parameter combos)
    assert file_info_df.filter(pl.col.rows.lt(14580)).height == 0, (
        "Data should not include files with less than 3240 rows (incomplete run)"
    )

    # max step 1500 was used for the full set fo 100 batches
    assert file_info_df.filter(pl.col.max_step.ne(1500)).height == 0, (
        "Data should only include files with max step of 1500"
    )
    # use to identify sepcific files:
    # file_info_df.filter(pl.col.max_step.ne(1500))
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
    run_groups_df = df.group_by(params["default"].keys()).agg(runs=pl.len())

    # we expect the same number of runs for each parameter set
    assert (run_groups_df["runs"].n_unique()) == 1

    runs_per_group = run_groups_df["runs"].max()

    run_groups_df
    return run_groups_df, runs_per_group


if __name__ == "__main__":
    app.run()
