# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "altair>=5.5.0,<6.0",
#   "pandas",
#   "marimo>=0.23.11",
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

    import marimo as mo

    if sys.platform == "emscripten":
        # Running in Pyodide/WASM.
        # mesa 2.1.5's __init__.py does
        # `from mesa_viz_tornado.ModularVisualization import *`
        # unconditionally. We never use that visualization layer (we draw with altair),
        # so stub it out before importing mesa to avoid the ModuleNotFoundError.
        import types

        _tornado_stub = types.ModuleType("mesa_viz_tornado")
        sys.modules["mesa_viz_tornado"] = _tornado_stub
        for submodule in [
            "ModularVisualization",
            "modules",
            "UserParam",
            "TextVisualization",
        ]:
            import_name = f"mesa_viz_tornado.{submodule}"
            setattr(_tornado_stub, submodule, types.ModuleType(import_name))
            sys.modules[import_name] = getattr(_tornado_stub, submodule)

        import micropip

        await micropip.install("mesa==2.1.5", deps=False)
        await micropip.install(["networkx", "numpy", "tqdm"])
        # uncomment and enable for local development involving app ui
        # await micropip.install(
        #     str(
        #         mo.notebook_location()
        #         / "public"
        #         / "simulatingrisk-1.1.0.dev1-py3-none-any.whl"
        #     )
        # )
        await micropip.install("simulatingrisk>=1.1.0", deps=False)

    from simulatingrisk.hawkdove.ui import (
        agent_portrayal,
        draw_hawkdove_agent_space,
    )
    from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel
    from simulatingrisk.hawkdovemulti.ui import ui_controls
    from simulatingrisk.hawkdovemulti.viz import (
        plot_agents_by_risk,
        plot_hawks_by_risk,
        plot_risklevel_changes,
        plot_wealth_by_risklevel,
    )
    from simulatingrisk.ui_common import init_control_buttons, init_refresh

    return (
        HawkDoveMultipleRiskModel,
        agent_portrayal,
        draw_hawkdove_agent_space,
        init_control_buttons,
        init_refresh,
        mo,
        plot_agents_by_risk,
        plot_hawks_by_risk,
        plot_risklevel_changes,
        plot_wealth_by_risklevel,
        ui_controls,
    )


@app.cell
def _(
    control_buttons,
    mo,
    refresh,
    simulation_display,
    simulation_status,
    ui_controls,
):
    mo.hstack(
        [
            mo.vstack(
                [
                    *ui_controls.values(),  # model parameters
                    mo.hstack(
                        control_buttons, gap=1, align="start"
                    ),  # simulation run/step/stop controls,
                    refresh,
                    simulation_status,
                    # make sure users know to reset to run with new parameters
                    mo.md("---\nⓘ Parameter changes take effect on **Reset**."),
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
    # display_step only updates every N steps for large grids, throttling chart re-renders.
    # The status bar uses step_count for accuracy; charts use display_step.
    display_step, set_display_step = mo.state(0)
    is_running, set_is_running = mo.state(False)
    # Remember the user's selected auto-refresh interval across pause/resume so
    # we can re-arm the refresh widget at the same speed when play is clicked.
    refresh_interval, set_refresh_interval = mo.state("0.5s")
    return (
        display_step,
        is_running,
        model_state,
        refresh_interval,
        set_display_step,
        set_is_running,
        set_model_state,
        set_refresh_interval,
        set_step_count,
        step_count,
    )


@app.cell
def _(init_control_buttons):
    # assign separately so we can watch the values of each button
    run_btn, pause_btn, step_btn, reset_btn = init_control_buttons()
    # combine for display in the UI
    control_buttons = run_btn, pause_btn, step_btn, reset_btn
    return control_buttons, pause_btn, reset_btn, run_btn, step_btn


@app.cell
def _(init_refresh, is_running, refresh_interval, set_refresh_interval):
    refresh = init_refresh(
        is_running=is_running(),
        refresh_interval=refresh_interval(),
        set_refresh_interval=set_refresh_interval,
    )
    return (refresh,)


@app.cell
def _(
    HawkDoveMultipleRiskModel,
    mo,
    pause_btn,
    reset_btn,
    run_btn,
    set_display_step,
    set_is_running,
    set_model_state,
    set_step_count,
    ui_controls,
):
    # Handle run / pause / reset button clicks.
    mo.stop(not any([run_btn.value, pause_btn.value, reset_btn.value]))

    if run_btn.value:
        set_is_running(True)
    elif pause_btn.value:
        set_is_running(False)
    elif reset_btn.value:
        _m = HawkDoveMultipleRiskModel(**{k: v.value for k, v in ui_controls.items()})
        set_model_state(_m)
        set_step_count(0)
        set_display_step(0)
        set_is_running(False)
    return


@app.cell
def _(
    HawkDoveMultipleRiskModel,
    is_running,
    mo,
    model_state,
    refresh,
    set_display_step,
    set_is_running,
    set_model_state,
    set_step_count,
    step_btn,
    ui_controls,
):
    # Advance the simulation. Triggered on every refresh tick and on step_btn click.
    # mo.stop exits when paused and the step button wasn't just pressed.
    refresh
    mo.stop(not (is_running() or step_btn.value))

    _model = model_state()
    if _model is None:
        _model = HawkDoveMultipleRiskModel(
            **{k: v.value for k, v in ui_controls.items()}
        )
        set_model_state(_model)

    if _model.running:
        _model.step()
        set_step_count(_model.schedule.steps)
        # throttle chart re-renders for large grids: only update display every N steps
        # always redraw on manual step so the user sees the result immediately
        _n = max(1, _model.grid.width * _model.grid.height // 500)
        if step_btn.value or _model.schedule.steps % _n == 0:
            set_display_step(_model.schedule.steps)
    else:
        set_is_running(False)
    return


@app.cell
def _(is_running, mo, model_state, step_count):
    _model = model_state()
    _step = step_count()
    _run_label = "▶ Running" if is_running() else "⏸ Paused"
    _sim_status = _model.status if _model else "not started"
    _n = max(1, _model.grid.width * _model.grid.height // 500) if _model else 1
    _refresh_note = f"\n\n_Charts refresh every {_n} steps._" if _n > 1 else ""
    simulation_status = mo.md(
        f"**Step:** {_step} | **Simulation:** {_run_label} | **Status:** {_sim_status}{_refresh_note}"
    )
    return (simulation_status,)


@app.cell
def _(
    agent_portrayal,
    display_step,
    draw_hawkdove_agent_space,
    mo,
    model_state,
    plot_agents_by_risk,
    plot_hawks_by_risk,
    plot_risklevel_changes,
    plot_wealth_by_risklevel,
):
    # Charts — depends on display_step, which is throttled for large grids to reduce re-renders.
    _step = display_step()
    _model = model_state()

    # smallest the agent grid should be displayed
    _min_grid_dimension = 275
    # width padding for legends
    _grid_width_padding = 75
    _min_grid_height = 325
    _grid_space_per_agent = 18

    if _model is None:
        simulation_display = mo.md(
            "_Click **▶ Run** or **⏭ Step** to start the simulation._"
        )
    else:
        _grid = draw_hawkdove_agent_space(_model, agent_portrayal)
        # set grid chart based on grid size (grid size = # agents in each dimension)
        # NOTE: set from model, not ui, since display must match current model
        # (changed ui values only applied on reset/restart)
        _grid_dimension = max(
            _grid_space_per_agent * _model.grid.width, _min_grid_dimension
        )
        _grid_height = max(_min_grid_height, _grid_dimension)

        _grid = _grid.properties(
            width=_grid_dimension + _grid_width_padding, height=_grid_height
        )

        _agent_df = (
            _model.datacollector.get_agent_vars_dataframe().reset_index().dropna()
        )

        _charts = [_grid]

        if not _agent_df.empty:
            _charts.append(plot_agents_by_risk(_model))
            _charts.append(plot_hawks_by_risk(_model))
            _charts.append(plot_wealth_by_risklevel(_model))
            _charts.append(plot_risklevel_changes(_model))

        # if grid is close to chart size, just flow all the charts together and wrap
        if _grid_dimension < 350:
            simulation_display = mo.hstack(_charts, gap=0, wrap=True)
        else:
            simulation_display = mo.hstack(
                [_grid, mo.hstack(_charts[1:], gap=0, wrap=True)], gap=0
            )
    return (simulation_display,)


if __name__ == "__main__":
    app.run()
