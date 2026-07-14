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
    # Parameter significance for Hawk/Dove with Evolving Risk-Attitudes

    To determine which parameters have an impact on the risk-attitudes in the population when the simulation converges, and to test the robustness of our model, we calculate the correlation between the varied simulation parameters and the percent of the population that is risk-seeking, risk-moderate, and risk-averse at the end of the simulation.
    """)
    return


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl
    from polars import col as c  # for short-hand column references
    import altair as alt

    data_dir = Path("data/default/")
    return alt, c, data_dir, mo, pl


@app.cell
def _(data_dir, pl):
    df = pl.scan_csv([str(file) for file in data_dir.glob("*_model.csv")]).collect()
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Calculate percentages for each group of risk attitudes:

    - Risk-Seeking : r = 0, 1, 2
    - Risk-Moderate : r = 3, 4, 5, 6
    - Risk-Averse : r = 7, 8, 9

    Then generate and graph a correlation matrix for the starting simulation parameters and those percentages.
    """)
    return


@app.cell(hide_code=True)
def _(c, df):
    # for each simulation run, calculate what percent of the population was risk seeking/moderate/averse
    # after all adjustments were made

    # limit to converged simulations only
    agent_risk_pcts_df = (
        df.filter(status="converged")
        .with_columns(
            total_r0=c.total_r0.fill_null(strategy="zero"),
            total_r9=c.total_r9.fill_null(strategy="zero"),
        )
        .with_columns(
            # r0 + r1 + r2
            pct_risk_inclined=(c.total_r0.add(c.total_r1.add(c.total_r2))).truediv(
                c.total_agents
            ),
            # r3 + r4 + r5 + r6
            pct_risk_moderate=(
                c.total_r3.add(c.total_r4).add(c.total_r5).add(c.total_r6)
            ).truediv(c.total_agents),
            # r7 + r8 + r9
            pct_risk_avoidant=(c.total_r7.add(c.total_r8).add(c.total_r9)).truediv(
                c.total_agents
            ),
        )
        .with_columns(
            # add total to make sure everything adds up correctly
            total_pct=c.pct_risk_inclined.add(
                c.pct_risk_moderate.add(c.pct_risk_avoidant)
            )
        )
    )

    # convert categorical variables into multiple true/false categories
    agent_risk_pcts_df = agent_risk_pcts_df.to_dummies("risk_distribution").to_dummies(
        "adjust_payoff"
    )

    # agent_risk_pcts_df
    return (agent_risk_pcts_df,)


@app.cell(hide_code=True)
def _(agent_risk_pcts_df, params, pl):

    # parameters we are interested in testing correlation
    corr_variables = ["pct_risk_inclined", "pct_risk_moderate", "pct_risk_avoidant"]

    param_variables = [
        p
        for p, val in params["default"].items()
        # omit categoricals we have converted and single-value params (no variance)
        if p not in ["risk_distribution", "adjust_payoff"]
        and isinstance(val, list)
        and len(val) > 1
    ]
    param_variables.extend(
        [
            c
            for c in agent_risk_pcts_df.columns
            if c.startswith("risk_distribution_") or c.startswith("adjust_payoff")
        ]
    )
    df_corr = agent_risk_pcts_df.select(*corr_variables, *param_variables).corr()

    # add row labels and order them first
    df_corr = df_corr.with_columns(pl.Series("var_x", df_corr.columns)).select(
        "var_x", *df_corr.columns
    )

    # df_corr
    return corr_variables, df_corr, param_variables


@app.cell(hide_code=True)
def _(c, corr_variables, df_corr, param_variables, pl):
    def param_group(param_name):
        # add group names to parameters so they can be displayed in logical groups
        if param_name.startswith("risk_distribution"):
            return "risk distribution"
        if param_name.endswith("neighborhood"):
            return "neighborhood size"
        if param_name.startswith("adjust_payoff"):
            return "adjust payoff"
        return ""

    df_corr_long = (
        df_corr.unpivot(
            on=df_corr.columns,
            index="var_x",
            variable_name="var_y",
            value_name="correlation",
        )
        .filter(c.var_y.is_in(corr_variables))
        .filter(c.var_x.is_in(param_variables))
        .with_columns(  # something is slightly off with the unpivot that we need this...
            correlation=c.correlation.cast(pl.Float32)
        )
        .with_columns(
            # add formatted correlation number for display
            correlation_str=pl.col.correlation.map_elements(
                lambda x: f"{x:,.2f}", return_dtype=pl.String
            )
        )
        .with_columns(
            group=c.var_x.map_elements(param_group, return_dtype=pl.String),
            # adjust parameter names for readability and avoid redundancy with group names
            var_x=pl.col("var_x")
            .str.replace_all("_neighborhood", "", literal=True)
            .str.replace_all("risk_distribution_", "", literal=True)
            .str.replace_all("adjust_payoff_", "", literal=True)
            .str.replace_all("_", " ", literal=True),
        )
    )
    # df_corr_long
    return (df_corr_long,)


@app.cell(hide_code=True)
def _(alt, df_corr_long, y_axis_sort):
    # flip the axes and display the chart longwise - easier to read

    _heatmap_corr_chart = (
        alt.Chart(df_corr_long)
        .mark_rect()
        .encode(
            y=alt.Y(
                "var_x:O",
                title=None,
            ),
            x=alt.X(
                "var_y:O",
                title="",  # Population Risk-Attitudes",
                sort=y_axis_sort,
                axis=alt.Axis(
                    orient="top",  # move axis to top
                    labelAngle=-25,  # angle the labels (negative = counterclockwise)
                    labelExpr="{'pct_risk_inclined': '% Risk-Seeking', 'pct_risk_moderate': '% Risk-Moderate', 'pct_risk_avoidant': '% Risk-Averse'}[datum.value]",
                ),
            ),
            # display color legend at bottom, match the chart width
            color=alt.Color("correlation")
            .scale(scheme="spectral", domain=[-0.43, 0.43])
            .legend(orient="bottom", gradientLength=350),
        )
    )

    _text_corr_chart = _heatmap_corr_chart.mark_text().encode(
        y="var_x:O",
        x=alt.X("var_y:O", sort=y_axis_sort),
        text="correlation_str",
        # for contrast, vary the color based on the intensity of the correlation, negative or positive
        color=alt.condition(
            "abs(datum.correlation) > 0.29", alt.value("white"), alt.value("black")
        ),
    )

    # facet by group so that so that related parameters can be compared together
    (_heatmap_corr_chart + _text_corr_chart).properties(
        width=350, height=alt.Step(30)
    ).facet(
        row=alt.Row("group:N", title=""),
        title="Parameter correlation with population risk attitudes",
    ).resolve_scale(y="independent")
    return


@app.cell(hide_code=True)
def _(alt, df_corr_long):
    # wide version of the correlation chart - uncomment last statement to view

    y_axis_sort = ["pct_risk_inclined", "pct_risk_moderate", "pct_risk_avoidant"]

    _heatmap_corr_chart = (
        alt.Chart(df_corr_long)
        .mark_rect()
        .encode(
            x=alt.X(
                "var_x:O",
                title=None,
                # title="Simulation Parameters",
                axis=alt.Axis(
                    orient="top",  # move axis to top
                    labelAngle=-45,  # angle the labels (negative = counterclockwise)
                ),
            ),
            y=alt.Y(
                "var_y:O",
                title="Population Risk-Attitudes",
                sort=y_axis_sort,
                axis=alt.Axis(
                    labelExpr="{'pct_risk_inclined': '% Risk-Seeking', 'pct_risk_moderate': '% Risk-Moderate', 'pct_risk_avoidant': '% Risk-Averse'}[datum.value]"
                ),
            ),
            color=alt.Color("correlation").scale(scheme="spectral", domainMid=0),
        )
    )

    _text_corr_chart = _heatmap_corr_chart.mark_text().encode(
        x="var_x:O",
        y=alt.Y("var_y:O", sort=y_axis_sort),
        text="correlation_str",
        # for contrast, vary the color based on the intensity of the correlation, negative or positive
        color=alt.condition(
            "abs(datum.correlation) > 0.29", alt.value("white"), alt.value("black")
        ),
    )

    # facet by group so that so that related parameters can be compared together
    # (_heatmap_corr_chart + _text_corr_chart).resolve_axis(y="shared").properties(
    #     width=alt.Step(55), height=300
    # ).facet(
    #     column=alt.Column("group:N", title="Parameter Group"),
    #     title="Simulation parameter correlation with population risk attitudes",
    # ).resolve_scale(x="independent")
    return (y_axis_sort,)


if __name__ == "__main__":
    app.run()
