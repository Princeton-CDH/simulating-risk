# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "altair>=5.5.0,<6.0",
#   "pandas",
#   "marimo>=0.23.11",
#   "simulatingrisk==1.0.0.post1",
# ]
# ///
# mesa and simulatingrisk are installed in the init cell below because mesa's
# dependency on tornado (a C-extension package) must be loaded from Pyodide's
# built-ins before micropip attempts to resolve it from PyPI.

import marimo

__generated_with = "0.23.11"
app = marimo.App(width="full")


@app.cell
async def _():
    import sys

    if sys.platform == "emscripten":
        # Running in Pyodide/WASM.
        # mesa 2.1.5's __init__.py does
        # `from mesa_viz_tornado.ModularVisualization import *`
        # unconditionally. We never use that visualization layer (we draw with altair),
        # so stub it out before importing mesa to avoid the ModuleNotFoundError.
        import types

        _stub = types.ModuleType("mesa_viz_tornado")
        _stub.ModularVisualization = types.ModuleType(
            "mesa_viz_tornado.ModularVisualization"
        )
        sys.modules["mesa_viz_tornado"] = _stub
        sys.modules[
            "mesa_viz_tornado.ModularVisualization"
        ] = _stub.ModularVisualization

        import micropip

        await micropip.install("mesa==2.1.5", deps=False)
        await micropip.install(["networkx", "numpy", "tqdm"])
        await micropip.install("simulatingrisk>=1.0.0", deps=False)
    return


@app.cell
def _():
    import marimo as mo
    import altair as alt
    from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel
    from simulatingrisk.hawkdove.server import (
        agent_portrayal,
        draw_hawkdove_agent_space,
    )
    from simulatingrisk.hawkdove.model import divergent_colors_10

    return (
        HawkDoveMultipleRiskModel,
        agent_portrayal,
        alt,
        divergent_colors_10,
        draw_hawkdove_agent_space,
        mo,
    )


@app.cell
def _(HawkDoveMultipleRiskModel, mo):
    params = mo.ui.dictionary(
        {
            "grid_size": mo.ui.slider(
                5, 40, value=10, step=1, label="Grid Size", show_value=True
            ),
            "risk_adjustment": mo.ui.dropdown(
                ["none", "adopt", "average"],
                value="adopt",
                label="Risk Adjustment",
            ),
            "risk_distribution": mo.ui.dropdown(
                list(HawkDoveMultipleRiskModel.risk_distribution_options),
                value="uniform",
                label="Risk Distribution",
            ),
            "adjust_every": mo.ui.slider(
                1, 30, value=10, step=1, label="Adjust Every N Rounds", show_value=True
            ),
            "hawk_odds": mo.ui.slider(
                0.0, 1.0, value=0.5, step=0.1, label="Hawk Odds", show_value=True
            ),
            "random_play_odds": mo.ui.slider(
                0.0,
                0.2,
                value=0.01,
                step=0.01,
                label="Random Play Odds",
                show_value=True,
            ),
        }
    )
    return (params,)


@app.cell
def _(
    control_buttons,
    mo,
    params,
    refresh,
    simulation_display,
    simulation_status,
):
    mo.hstack(
        [
            mo.vstack(
                [
                    *params.values(),  # model parameters
                    mo.hstack(
                        control_buttons, gap=1, align="start"
                    ),  # simulation run/step/stop controls,
                    refresh,
                    simulation_status,
                ]
            ),
            simulation_display,
        ],
        widths=[1, 4],
        align="start",
    )

    return


@app.cell
def _(mo):
    # Mutable simulation state — step_count increments on each model step,
    # which causes the chart cell to re-run and redraw.
    model_state, set_model_state = mo.state(None)
    step_count, set_step_count = mo.state(0)
    is_running, set_is_running = mo.state(False)
    return (
        is_running,
        model_state,
        set_is_running,
        set_model_state,
        set_step_count,
        step_count,
    )


@app.cell
def _(mo):
    run_btn = mo.ui.run_button(label="▶ Run")
    pause_btn = mo.ui.run_button(label="⏸ Pause")
    step_btn = mo.ui.run_button(label="⏭ Step")
    reset_btn = mo.ui.run_button(label="⏹ Reset")

    control_buttons = [run_btn, pause_btn, step_btn, reset_btn]
    return control_buttons, pause_btn, reset_btn, run_btn, step_btn


@app.cell
def _(mo):
    # Speed selector for auto-run interval
    refresh = mo.ui.refresh(
        default_interval="0.5s", options=["0.1s", "0.2s", "0.5s", "1s", "2s"]
    )

    return (refresh,)


@app.cell
def _(
    HawkDoveMultipleRiskModel,
    mo,
    params,
    pause_btn,
    reset_btn,
    run_btn,
    set_is_running,
    set_model_state,
    set_step_count,
):
    # Handle run / pause / reset button clicks.
    mo.stop(not any([run_btn.value, pause_btn.value, reset_btn.value]))

    if run_btn.value:
        set_is_running(True)
    elif pause_btn.value:
        set_is_running(False)
    elif reset_btn.value:
        _m = HawkDoveMultipleRiskModel(**{k: v.value for k, v in params.items()})
        set_model_state(_m)
        set_step_count(0)
        set_is_running(False)
    return


@app.cell
def _(
    HawkDoveMultipleRiskModel,
    is_running,
    mo,
    model_state,
    params,
    refresh,
    set_is_running,
    set_model_state,
    set_step_count,
    step_btn,
):
    # Advance the simulation. Triggered on every refresh tick and on step_btn click.
    # mo.stop exits when paused and the step button wasn't just pressed.
    refresh
    mo.stop(not (is_running() or step_btn.value))

    _model = model_state()
    if _model is None:
        _model = HawkDoveMultipleRiskModel(**{k: v.value for k, v in params.items()})
        set_model_state(_model)

    if _model.running:
        _model.step()
        set_step_count(_model.schedule.steps)
    else:
        set_is_running(False)
    return


@app.cell
def _(is_running, mo, model_state, step_count):
    _model = model_state()
    _step = step_count()
    _run_label = "▶ Running" if is_running() else "⏸ Paused"
    _sim_status = _model.status if _model else "not started"
    simulation_status = mo.md(
        f"**Step:** {_step} | **Simulation:** {_run_label} | **Status:** {_sim_status}"
    )
    return (simulation_status,)


@app.cell
def _(
    agent_portrayal,
    alt,
    divergent_colors_10,
    draw_hawkdove_agent_space,
    mo,
    model_state,
    step_count,
):
    # Charts — depends on step_count so this cell re-runs on every model step.
    _step = step_count()
    _model = model_state()

    if _model is None:
        simulation_display = mo.md(
            "_Click **▶ Run** or **⏭ Step** to start the simulation._"
        )
    else:
        _grid = draw_hawkdove_agent_space(_model, agent_portrayal)

        _agent_df = (
            _model.datacollector.get_agent_vars_dataframe().reset_index().dropna()
        )
        _model_df = _model.datacollector.get_model_vars_dataframe().reset_index()

        _charts = [_grid]

        if not _agent_df.empty:
            _last_step = _agent_df.Step.max()
            _last_round = _agent_df[_agent_df.Step == _last_step]
            _by_risk = _last_round.groupby("risk_level", as_index=False).agg(
                total=("AgentID", "count")
            )
            _bar = (
                alt.Chart(_by_risk)
                .mark_bar(width=14)
                .encode(
                    x=alt.X(
                        "risk_level",
                        title="Risk Attitude",
                        axis=alt.Axis(tickCount=10),
                        scale=alt.Scale(domain=[0, 9]),
                    ),
                    y=alt.Y("total", title="Agents"),
                    color=alt.Color("risk_level:N", legend=None).scale(
                        domain=list(range(10)), range=divergent_colors_10
                    ),
                )
                .properties(title="Agents by Risk Attitude", width=280, height=180)
            )
            _charts.append(_bar)

        if not _model_df.empty:
            _hawk_df = _model_df.dropna(subset=["percent_hawk"])
            if not _hawk_df.empty:
                _line = (
                    alt.Chart(_hawk_df)
                    .mark_line()
                    .encode(
                        x=alt.X("index", title="Step"),
                        y=alt.Y(
                            "percent_hawk",
                            title="% Hawk",
                            scale=alt.Scale(domain=[0, 1]),
                        ),
                    )
                    .properties(title="Percent Hawk", width=280, height=180)
                )
                _rolling = _model_df.dropna(subset=["rolling_percent_hawk"])
                if not _rolling.empty:
                    _line = _line + alt.Chart(_rolling).mark_line(
                        strokeDash=[4, 2], color="gray"
                    ).encode(
                        x=alt.X("index"),
                        y=alt.Y("rolling_percent_hawk"),
                    )
                _charts.append(_line)

        simulation_display = mo.hstack(_charts, gap=2)

    return (simulation_display,)


if __name__ == "__main__":
    app.run()
