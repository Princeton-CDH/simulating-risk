import marimo

__generated_with = "0.23.11"
app = marimo.App(
    width="medium",
    app_title="Hawk/Dove with Multiple Risk-Attitudes - Payoff Analysis",
    html_head_file="../docs_head.html",
)


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
def _():
    from simulatingrisk.doc_utils import docs_header

    docs_header()
    return


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
def _(data_dir, params, pl):
    # agent data accompanies model data with same filename; run ids are only unique within a filename, and model
    # data includes all the parameters for that run

    def load_agent_data() -> list[pl.LazyFrame]:
        # load agent data and model data in pairs by filename, joining on RunId
        data_lf = []
        for model_file in data_dir.glob("*_model.csv"):
            # batch run filename shared by model/agent data; runid is unique within a batch
            batchrun_base_name = model_file.stem.replace("_model", "")
            agent_file = model_file.with_name(f"{batchrun_base_name}_agent.csv")
            if not agent_file.exists() or agent_file.stat().st_size == 0:
                print(f"Missing or empty agent file at {agent_file}")
                return None

            # load model data and join with agent data, then subset to the columns needed for analysis
            # - limit to initial parameters and RunId for joining with model data
            model_df = pl.scan_csv(str(model_file)).select(
                "RunId", *params["no_adjustment"].keys()
            )
            # drop risk_level_changed; not relevant here (no adjustment = no changes)
            # rename internal risk_level field to risk_attitude
            agent_df = (
                pl.scan_csv(str(agent_file))
                .drop("risk_level_changed")
                .rename({"risk_level": "risk_attitude"})
            )
            # join agent data with model data and add to list of lazy frames
            # make runid unique by adding base filename
            agent_df = (
                agent_df.join(model_df, on=["RunId"], how="left")
                .with_columns(
                    run_id=pl.concat_str(
                        [pl.col.RunId, pl.lit(model_file.stem.replace("_model", ""))],
                        separator="|",
                    )
                )
                .drop("RunId")
            )

            data_lf.append(agent_df)

        return data_lf

    model_agent_df = (
        pl.concat(load_agent_data())
        .with_columns(
            # calculate a scaled points value so we can compare across runs with different length and play neighborhood
            scaled_points=pl.col("points")
            .truediv(pl.col("play_neighborhood"))
            .truediv(pl.col("Step"))
            .mul(100)
        )
        .collect()
    )
    model_agent_df
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

    # param_level
    param_level
    # corr = param_level.corr()

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
    run_corr_matrix_df
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
    run_corr_matrix_long_df
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
def _(payoff_by_risk_grid, plot_mean_quartiles):
    plot_mean_quartiles(payoff_by_risk_grid, "grid_size", "Grid Size")
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
def _(payoff_by_risk_playnhood, plot_mean_quartiles):
    plot_mean_quartiles(
        payoff_by_risk_playnhood, "play_neighborhood", "Play Neighborhood"
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
def _(payoff_by_risk_obsvnhood, plot_mean_quartiles):
    plot_mean_quartiles(
        payoff_by_risk_obsvnhood, "observed_neighborhood", "Observed Neighborhood"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    Utility methods used to graph data.
    """)
    return


@app.cell
def _(alt, mo, pl):
    # define a custom box plot method using layered plots,
    # so that we can quickly generate plots from statistics generated by polars

    def custom_boxplot(df):
        # calculate risk group labels, for color
        plot_df = df.with_columns(
            risk_type=pl.when(pl.col.risk_attitude < 3)
            .then(pl.lit("Risk-Seeking"))
            .when(pl.col.risk_attitude < 7)
            .then(pl.lit("Risk-Moderate"))
            .otherwise(pl.lit("Risk-Averse"))
        )
        # create base chart to use across layers
        base_chart = alt.Chart(plot_df)

        # area chart for Q1 to Q3
        area_chart = base_chart.mark_rect(width=15).encode(
            y=alt.Y("Q1").axis(
                offset=12
            ),  # add offset so axis does not crowd rectangle
            y2="Q3",
            x=alt.X("risk_attitude:Q", title="Risk Attitude"),
            tooltip=["min", "max", "mean", "Q1", "median", "Q3"],
            # colors from tableau 10 https://vega.github.io/vega/docs/schemes/#tableau10
            # but specify order to make more logical/semantic
            color=alt.Color(
                "risk_type",
                title="Risk Attitude",
                sort=["Risk Inclined", "Risk Moderate", "Risk Avoidant"],
            ).scale(range=["#e45756", "#f58518", "#4c78a8"]),
        )
        # line chart for min-max spread
        # specifying a stroke for point on the line only adds the min point

        # set light/dark color depending on notebook theme
        line_stroke_color = " #52514e" if mo.app_meta().theme == "light" else "#c3c2b7"

        minmax_line_chart = base_chart.mark_line(
            point=alt.OverlayMarkDef(
                filled=False, shape="stroke", color=line_stroke_color, strokeWidth=2
            )
        ).encode(alt.Y("min"), alt.Y2("max"), x="risk_attitude:Q")
        # add a black stroke for the max
        max_marks = base_chart.mark_point(
            shape="stroke", size=55, color=line_stroke_color
        ).encode(
            y="max",
            x=alt.X("risk_attitude:Q"),
        )

        median_marks = base_chart.mark_point(
            shape="stroke", size=100, strokeWidth=1, color=line_stroke_color
        ).encode(y="median", x="risk_attitude:Q")

        # mean line ?
        mean_line_chart = base_chart.mark_line(
            interpolate="monotone", color=line_stroke_color, opacity=0.5
        ).encode(
            x=alt.X("risk_attitude:Q"),
            y=alt.Y("mean", title="Cumulative Payoff").scale(zero=False),
        )

        return (
            mean_line_chart + minmax_line_chart + area_chart + median_marks + max_marks
        ).resolve_axis("shared")

    return (custom_boxplot,)


@app.cell
def _(alt, payoffchart_title):
    # define a custom method to plot mean and quartiles for a specified simulation parameter

    def plot_mean_quartiles(df, field, field_label):
        # takes a dataframe, the field in the dataframe for the simulation parameter, and displayable label for the field

        # create a selection filter bound to the legend
        selection = alt.selection_point(fields=[field], bind="legend")
        base_chart = alt.Chart(df)
        # curved line for the mean pyoff by risk attitude
        payoff_mean_chart = base_chart.mark_line(interpolate="monotone").encode(
            x=alt.X("risk_attitude", title="Risk Attitude").scale(domain=[0, 9]),
            y=alt.Y("mean", title="Cumulative Payoff (mean)").scale(zero=False),
            color=alt.Color(f"{field}:N", title=field_label),
            opacity=alt.when(selection).then(alt.value(1.0)).otherwise(alt.value(0.4)),
        )
        # curved area chart for payoff quartile spread
        payoff_spread = base_chart.mark_area(interpolate="monotone").encode(
            x=alt.X("risk_attitude", title="Risk Attitude").scale(domain=[0, 9]),
            y=alt.Y("Q3").scale(zero=False),
            y2="Q1",
            color=alt.Color(f"{field}:N", title=field_label),
            opacity=alt.when(selection).then(alt.value(0.3)).otherwise(alt.value(0.1)),
        )

        # combine the charts for multiple ways to view
        chart_payoff_title = payoffchart_title.copy()
        chart_payoff_title["text"] = (
            f"{payoffchart_title['text']} and {field_label} — Mean and Quartiles"
        )

        # display mean curve chart, payoff area chart, and mean layered with the payoff
        return (
            (payoff_mean_chart | payoff_spread | (payoff_mean_chart + payoff_spread))
            .add_params(selection)
            .resolve_legend(color="shared")
            .properties(title=chart_payoff_title)
        )

    return (plot_mean_quartiles,)


if __name__ == "__main__":
    app.run()
