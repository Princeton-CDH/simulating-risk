import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    from simulatingrisk.doc_utils import docs_header
    from simulatingrisk.hawkdovemulti.batch_run import params

    docs_header()
    return (params,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Percent of the time agents play Hawk, by risk attitude

    What % of the time do risk-seeking (R=1) and risk-averse (R8) agents play Hawk?

    - Our guess from observation is is >90% for R=1, <10% for R8, but it would be helpful to have statistics for this: for X trials, how many of them does R1 play Hawk more than 90% of the time?
    - Also useful to have statistics e.g. R=2 played Hawk between 80-90% of the time, or whatever the result is.
    """)
    return


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    import altair as alt

    # shared notebook code in this folder
    from utils import load_agent_data

    data_dir = Path("data/no_adjustment/")
    return alt, data_dir, load_agent_data, mo, pl


@app.cell(hide_code=True)
def _(data_dir, load_agent_data, pl):
    # load agent data combined with model parameters
    model_agent_df = (
        pl.concat(load_agent_data(data_dir))
        .with_columns(
            # the hawk_count column reports how many times this agent played hawk; divide by run length (step count) for percent
            pct_hawk_plays=pl.col.hawk_count.truediv(pl.col.Step).mul(100)
        )
        .collect()
    )
    return (model_agent_df,)


@app.cell(hide_code=True)
def _(model_agent_df, pl):
    # group by risk attitude and get an average of the percents for each group
    hawk_by_risk_attitude = model_agent_df.group_by("risk_attitude").agg(
        avg_pct_hawk_plays=pl.col.pct_hawk_plays.mean()
    )

    # output results fields as nicely styled table
    (
        hawk_by_risk_attitude.select("risk_attitude", "avg_pct_hawk_plays")
        .sort("risk_attitude")
        .rename(
            {"risk_attitude": "Risk Attitude", "avg_pct_hawk_plays": "% plays Hawk"}
        )
        .style.tab_header(title="% of time agents play Hawk by Risk Attitude")
        .fmt_number("% plays Hawk", decimals=1)
    )

    return (hawk_by_risk_attitude,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can output the same percentages as a bar chart or a heatmap, for comparison.
    """)
    return


@app.cell(hide_code=True)
def _(alt, hawk_by_risk_attitude):
    alt.Chart(hawk_by_risk_attitude).mark_bar(width=10).encode(
        x=alt.X("risk_attitude", title="Risk Attitude").scale(domain=[0, 9]),
        y=alt.Y("avg_pct_hawk_plays", title="% time plays Hawk"),
    ).properties(title="% of time agents play Hawk")
    return


@app.cell(hide_code=True)
def _(alt, hawk_by_risk_attitude):
    alt.Chart(hawk_by_risk_attitude).mark_rule(strokeWidth=40).encode(
        x=alt.X("risk_attitude", title="Risk Attitude").scale(domain=[0, 9]),
        # y=alt.value(0),
        # y2=alt.value(15),
        color=alt.Color("avg_pct_hawk_plays:Q", title="% time plays Hawk")
        .scale(scheme="spectral", domain=[100.0, 0.0])
        .legend(orient="bottom", gradientLength=350),
    ).properties(title="Average % of time agents play Hawk by Risk-Attitude", width=350)
    return


@app.cell(hide_code=True)
def _(model_agent_df, params, pl):
    # one row per run_id — mean scaled_points across all agents in that run

    # parameters to test correlation
    corr_variables = ["pct_hawk_plays"]

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

    # corr_sample_size = 100_000   # completes in 17.20s
    corr_sample_size = 1_000_000  # completes in 32.69s

    # group by risk attitude and parameters
    risk_attitude_percents = (
        _model_agent_riskdist_df.sample(corr_sample_size)
        .group_by("risk_attitude", *param_variables)
        .agg(pct_hawk_plays=pl.col.pct_hawk_plays.mean())
    )

    _corr_cols = risk_attitude_percents.columns

    corr_df = (
        risk_attitude_percents.corr()
        .with_columns(pl.Series("var_x", _corr_cols))
        .select("var_x", *_corr_cols)
    )
    # corr_df
    return corr_df, corr_sample_size, corr_variables


@app.cell(hide_code=True)
def _(corr_df, corr_variables, pl):
    def param_group(param_name):
        # add group names to parameters so they can be displayed in logical groups
        if param_name.startswith("risk_distribution"):
            return "risk distribution"
        if param_name.endswith("neighborhood"):
            return "neighborhood size"
        if param_name.startswith("adjust_payoff"):
            return "adjust payoff"
        return ""

    # add columns as label, then unpivot to long form for charting
    corr_matrix_long_df = (
        corr_df.unpivot(
            on=corr_df.columns,
            index="var_x",
            variable_name="var_y",
            value_name="correlation",
        )
        .filter(pl.col.var_y.is_in(corr_variables))
        .filter(~pl.col.var_x.is_in(corr_variables))
        .with_columns(
            correlation=pl.col.correlation.cast(pl.Float32),
            correlation_str=pl.col.correlation.map_elements(
                lambda x: f"{float(x):,.2f}", return_dtype=pl.String
            ),
        )
        .with_columns(
            group=pl.col.var_x.map_elements(param_group, return_dtype=pl.String),
            # adjust parameter names for readability and avoid redundancy with group names
            var_x=pl.col("var_x")
            .str.replace_all("_neighborhood", "", literal=True)
            .str.replace_all("risk_distribution_", "", literal=True)
            .str.replace_all("adjust_payoff_", "", literal=True)
            .str.replace_all("_", " ", literal=True),
        )
    )
    # corr_matrix_long_df
    return (corr_matrix_long_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We aggregate hawk-play percentages by risk attitude across unique parameter combinations to check for correlations with other parameters.

    The only signal is a strong negative correlation between risk-attitude and % of time agents play hawk, which we expect (higher numeric risk-attitudes are increasing risk-averse, so they play hawk less frequently).  The slight correlation with the skewed risk distributions are a reflection of the risk-attitudes present in the population.
    """)
    return


@app.cell(hide_code=True)
def _(alt, corr_matrix_long_df, corr_sample_size):

    _heatmap_corr_chart = (
        alt.Chart(corr_matrix_long_df)
        .mark_rect()
        .encode(
            y=alt.Y(
                "var_x:O",
                title="",
            ),
            x=alt.X(
                "var_y:O",
                title="",
                axis=alt.Axis(
                    orient="top",  # move axis to top
                    labelAngle=0,  # angle the labels (negative = counterclockwise)
                    labelExpr="{'pct_hawk_plays': '% Hawk plays'}[datum.value]",
                ),
            ),
            # use spectral theme since we have both negative and positive correlations
            color=alt.Color("correlation")
            .scale(scheme="spectral")
            .legend(orient="bottom", gradientLength=250),
        )
    )

    _text_corr_chart = _heatmap_corr_chart.mark_text().encode(
        y="var_x:O",
        x="var_y:O",
        text="correlation_str",
        # for contrast, vary the color based on the intensity of the correlation, negative or positive
        color=alt.condition(
            "abs(datum.correlation) > 0.3", alt.value("white"), alt.value("black")
        ),
    )

    (_heatmap_corr_chart + _text_corr_chart).properties(width=250).facet(
        row=alt.Row("group:N", title=""),
        title=f"Parameter correlation with % of time agents play hawk (sample of {corr_sample_size:,} agents)",
    ).resolve_scale(y="independent")
    return


if __name__ == "__main__":
    app.run()
