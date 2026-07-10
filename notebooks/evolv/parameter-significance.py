import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import polars as pl
    from polars import col as c  # for short-hand column references
    import altair as alt

    data_dir = Path("data/default/")

    return alt, c, data_dir, pl


@app.cell
def _(data_dir, pl):
    df = pl.scan_csv([str(file) for file in data_dir.glob("*_model.csv")]).collect()
    df
    return (df,)


@app.cell
def _(c, df):
    agent_risk_pcts_df = df.with_columns(
        total_r0=c.total_r0.fill_null(strategy="zero"),
        total_r9=c.total_r9.fill_null(strategy="zero"),
    ).with_columns(
        pct_risk_inclined=c.total_r0.add((c.total_r1).add(c.total_r2)).truediv(
            c.total_agents
        ),
        pct_risk_moderate=c.total_r0.add(
            (c.total_r3).add(c.total_r4).add(c.total_r6)
        ).truediv(c.total_agents),
        pct_risk_avoidant=c.total_r0.add(
            (c.total_r7).add(c.total_r8).add(c.total_r9)
        ).truediv(c.total_agents),
    )
    agent_risk_pcts_df
    return (agent_risk_pcts_df,)


@app.cell
def _(agent_risk_pcts_df):
    agent_risk_pcts_df.to_dummies("risk_distribution").to_dummies(
        "adjust_payoff"
    ).to_dummies("include_endpoints").to_dummies("adjust_payoff")
    return


@app.cell
def _(agent_risk_pcts_df, pl):

    param_categ_df = (
        agent_risk_pcts_df.to_dummies("risk_distribution")
        .to_dummies("adjust_payoff")
        .to_dummies("include_endpoints")
    )

    df_corr = param_categ_df.select(
        "pct_risk_inclined",
        "pct_risk_moderate",
        "pct_risk_avoidant",
        "grid_size",
        "hawk_odds",
        "play_neighborhood",
        "observed_neighborhood",
        "adjust_neighborhood",
        "random_play_odds",
        "include_endpoints_true",
        "include_endpoints_false",
        "risk_distribution_uniform",
        "risk_distribution_normal",
        "risk_distribution_skewed left",
        "risk_distribution_skewed right",
        "risk_distribution_bimodal",
        "adjust_payoff_recent",
        "adjust_payoff_total",
    ).corr()

    cols = df_corr.columns
    df_corr = df_corr.with_columns(pl.Series("param", cols)).select(
        "param", *cols
    )  # add row labels and order it first

    df_corr
    return cols, df_corr


@app.cell
def _(c, cols, df_corr):
    df_corr_long = (
        df_corr.unpivot(
            on=cols,
            index="param",
            variable_name="var_y",
            value_name="correlation",
        )
        .filter(
            c.param.is_in(
                ["pct_risk_inclined", "pct_risk_moderate", "pct_risk_avoidant"]
            )
        )
        .filter(
            ~c.var_y.is_in(
                ["pct_risk_inclined", "pct_risk_moderate", "pct_risk_avoidant"]
            )
        )
    )
    df_corr_long
    return (df_corr_long,)


@app.cell
def _(alt, df_corr_long):

    alt.Chart(df_corr_long).mark_rect().encode(
        x="param:O",
        y="var_y:O",
        color=alt.Color("correlation").scale(scheme="spectral"),  # maybe brownbluegreen
    ).properties(width=300, height=350)
    return


if __name__ == "__main__":
    app.run()
