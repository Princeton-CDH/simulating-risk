import marimo

__generated_with = "0.23.11"
app = marimo.App(
    width="medium",
    app_title="Hawk/Dove with Multiple Risk-Attitudes - Payoff Analysis",
    html_head_file="../docs_head.html",
)


@app.cell
def _():
    from simulatingrisk.doc_utils import docs_header

    docs_header()
    return


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt

    from simulatingrisk.hawkdovemulti.batch_run import params

    # shared notebook code in this folder
    from utils import custom_boxplot, plot_mean_quartiles, load_agent_data

    data_dir = Path("data/no_adjustment/")
    return (
        alt,
        custom_boxplot,
        data_dir,
        mo,
        params,
        pl,
        plot_mean_quartiles,
        load_agent_data,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Hawk/Dove with Multiple Risk-Attitudes : Payoff Analysis

    - mean and quartiles for payoff by risk attitude
    - does mean vary between different risk attitudes or is it roughly the same?
     - quartiles look different, but need a statistic; esp. compare lower-R quartile to higher-R quartile
      - expect/hope that lower quartile is higher for R1 than R8, higher quartile is higher for R8 than R1
      - what's going on in the middle?


    Simulations run for different lengths before converging, simulations include a range of different play neighborhood sizes (which affects total payoff, since each agent plays all neighbors in their play neighborhood. Therefore, we scale payoff by play neighborhood size and simulation run length so that payoffs can be compared across simulations.  The scaled points is multipled by 100 to make the point ranges more intelligible and comparable to a simulation run.

    \[
     scaled\_points = ((points / play\_neighborhood) / simulation\_runlength) * 100
    \]
    """)
    return


@app.cell
def _(data_dir, pl, load_agent_data):

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


@app.cell
def _():
    # sns.boxenplot(data=model_agent_df, y="points", x="risk_level")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Mean, median, and quartiles for payoff by risk-attitude
    """)
    return


@app.cell
def _(model_agent_df, pl):
    # Calculate quartiles with polars
    payoff_by_risk_attitude = (
        model_agent_df.group_by("risk_attitude")
        .agg(
            min=pl.col("scaled_points").min(),
            max=pl.col("scaled_points").max(),
            median=pl.col("scaled_points").median(),
            mean=pl.col("scaled_points").mean(),
            Q1=pl.col("scaled_points").quantile(0.25),
            Q2=pl.col("scaled_points").quantile(0.5),
            Q3=pl.col("scaled_points").quantile(0.75),
        )
        .sort("risk_attitude")
    )

    payoff_by_risk_attitude
    return (payoff_by_risk_attitude,)


@app.cell
def _(alt, custom_boxplot, payoff_by_risk_attitude):
    payoffchart_title = alt.TitleParams(
        "Cumulative Payoff Distribution by Risk Attitude",
        subtitle="Payoff scaled by simulation length and play neighborhood across all simulations",
    )

    custom_boxplot(payoff_by_risk_attitude).properties(title=payoffchart_title)
    return (payoffchart_title,)


@app.cell
def _(payoff_by_risk_attitude):
    # output payoff by risk attitude as nicely styled table
    (
        payoff_by_risk_attitude.rename({"risk_attitude": "Risk Attitude"})
        .style.tab_header(
            title="Cumulative Payoff by Risk Attitude",
            subtitle="Payoff scaled by simulation length and play neighborhood",
        )
        .fmt_number(decimals=1)
        .fmt_number("Risk Attitude", decimals=0)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Payoff and simulation parameters

    How is agent payoff affected by simulation parameters?
    """)
    return


@app.cell
def _(model_agent_df, params, pl):
    # one row per run_id — mean scaled_points across all agents in that run

    # parameters to test correlation
    corr_variables = ["q1_payoff", "mean_payoff", "q3_payoff"]

    param_variables = [
        p
        for p in params["no_adjustment"].keys()
        if p not in ["risk_distribution", "risk_adjustment"]
    ]

    # risk distribution is categorical; treat to one-hot 0/1 for each
    _model_agent_riskdist_df = model_agent_df.to_dummies("risk_distribution")
    # print(_model_agent_riskdist_df.columns)
    param_variables.extend(
        [
            c
            for c in _model_agent_riskdist_df.columns
            if c.startswith("risk_distribution_")
        ]
    )
    # print(corr_variables)

    # corr_sample_size = 100_000   # completes in 17.20s
    corr_sample_size = 1_000_000  # completes in 32.69s

    param_level = (
        _model_agent_riskdist_df.sample(corr_sample_size)
        .group_by("run_id", *param_variables)
        .agg(
            mean_payoff=pl.col.scaled_points.mean(),
            q1_payoff=pl.col.scaled_points.quantile(0.25),
            q3_payoff=pl.col.scaled_points.quantile(0.75),
        )
    )
    return corr_sample_size, corr_variables, param_level, param_variables


@app.cell(hide_code=True)
def _(corr_variables, param_level, param_variables, pl):
    _corr_cols = corr_variables + param_variables

    run_corr_matrix_df = (
        param_level.select(_corr_cols)
        # add labels
        .corr()
        .with_columns(pl.Series("var_x", _corr_cols))
        .select("var_x", *_corr_cols)
    )
    return (run_corr_matrix_df,)


@app.cell
def _(pl, run_corr_matrix_df):

    # add columns as label, then unpivot to long form for charting
    run_corr_matrix_long_df = (
        run_corr_matrix_df.unpivot(
            on=run_corr_matrix_df.columns,
            index="var_x",
            variable_name="var_y",
            value_name="correlation",
        )
        .filter(pl.col.var_y.is_in(["mean_payoff", "q1_payoff", "q3_payoff"]))
        .filter(~pl.col.var_x.is_in(["mean_payoff", "q1_payoff", "q3_payoff"]))
        .with_columns(
            correlation=pl.col.correlation.cast(pl.Float32),
            correlation_str=pl.col.correlation.map_elements(
                lambda x: f"{float(x):,.2f}", return_dtype=pl.String
            ),
        )
    )
    return (run_corr_matrix_long_df,)


@app.cell
def _(alt, corr_sample_size, run_corr_matrix_long_df):

    _heatmap_corr_chart = (
        alt.Chart(run_corr_matrix_long_df)
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
            color=alt.Color("correlation", scale=alt.Scale(scheme="spectral")),
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

    (_heatmap_corr_chart + _text_corr_chart).properties(
        width=600,
        title=f"Payoff / parameter correlation (based on sample of {corr_sample_size:,} agents)",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Grid Size
    """)
    return


@app.cell
def _(model_agent_df, pl):
    # calculate mean & quartiles for risk attitude by grid size
    payoff_by_risk_grid = (
        model_agent_df.group_by("risk_attitude", "grid_size")
        .agg(
            min=pl.col("scaled_points").min(),
            max=pl.col("scaled_points").max(),
            median=pl.col("scaled_points").median(),
            mean=pl.col("scaled_points").mean(),
            Q1=pl.col("scaled_points").quantile(0.25),
            Q2=pl.col("scaled_points").quantile(0.5),
            Q3=pl.col("scaled_points").quantile(0.75),
        )
        .sort("grid_size", "risk_attitude")
    )
    return (payoff_by_risk_grid,)


@app.cell
def _(alt, custom_boxplot, payoff_by_risk_grid, payoffchart_title):
    custom_boxplot(payoff_by_risk_grid).facet(
        column=alt.Column("grid_size", title="Grid Size")
    ).properties(title=payoffchart_title)
    return


@app.cell
def _(payoff_by_risk_grid, payoffchart_title, plot_mean_quartiles):
    plot_mean_quartiles(
        payoff_by_risk_grid, "grid_size", "Grid Size", payoffchart_title
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Play Neighborhood
    """)
    return


@app.cell
def _(alt, custom_boxplot, model_agent_df, payoffchart_title, pl):
    # calculate mean & quartiles for risk attitude by play neighborhood
    payoff_by_risk_playnhood = (
        model_agent_df.group_by("risk_attitude", "play_neighborhood")
        .agg(
            min=pl.col("scaled_points").min(),
            max=pl.col("scaled_points").max(),
            median=pl.col("scaled_points").median(),
            mean=pl.col("scaled_points").mean(),
            Q1=pl.col("scaled_points").quantile(0.25),
            Q2=pl.col("scaled_points").quantile(0.5),
            Q3=pl.col("scaled_points").quantile(0.75),
        )
        .sort("play_neighborhood", "risk_attitude")
    )

    custom_boxplot(payoff_by_risk_playnhood).facet(
        column=alt.Column("play_neighborhood", title="Play Neighborhood")
    ).properties(title=payoffchart_title)
    return (payoff_by_risk_playnhood,)


@app.cell
def _(payoff_by_risk_playnhood, payoffchart_title, plot_mean_quartiles):
    plot_mean_quartiles(
        payoff_by_risk_playnhood,
        "play_neighborhood",
        "Play Neighborhood",
        payoffchart_title,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Observed Neighborhood
    """)
    return


@app.cell
def _(model_agent_df, pl):

    # calculate mean & quartiles for risk attitude by observed neighborhood
    payoff_by_risk_obsvnhood = (
        model_agent_df.group_by("risk_attitude", "observed_neighborhood")
        .agg(
            min=pl.col("scaled_points").min(),
            max=pl.col("scaled_points").max(),
            median=pl.col("scaled_points").median(),
            mean=pl.col("scaled_points").mean(),
            Q1=pl.col("scaled_points").quantile(0.25),
            Q2=pl.col("scaled_points").quantile(0.5),
            Q3=pl.col("scaled_points").quantile(0.75),
        )
        .sort("observed_neighborhood", "risk_attitude")
    )
    return (payoff_by_risk_obsvnhood,)


@app.cell
def _(alt, custom_boxplot, payoff_by_risk_obsvnhood, payoffchart_title):
    custom_boxplot(payoff_by_risk_obsvnhood).facet(
        column=alt.Column("observed_neighborhood", title="Observed Neighborhood")
    ).properties(title=payoffchart_title)
    return


@app.cell
def _(payoff_by_risk_obsvnhood, payoffchart_title, plot_mean_quartiles):
    plot_mean_quartiles(
        payoff_by_risk_obsvnhood,
        "observed_neighborhood",
        "Observed Neighborhood",
        payoffchart_title,
    )
    return


if __name__ == "__main__":
    app.run()
