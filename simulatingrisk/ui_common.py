"""
Reusable marimo UI helpers shared across simulation apps.

These build common simulation-control widgets (run/pause/step/reset buttons
and the auto-refresh speed selector). They are intentionally generic and
don't depend on any particular model.
"""

import marimo as mo

#: Available auto-refresh intervals for the speed selector.
REFRESH_INTERVAL_OPTIONS = ["0.1s", "0.2s", "0.5s", "1s", "2s"]


def init_control_buttons() -> tuple[mo.ui.run_button, ...]:
    """Build the run / pause / step / reset control buttons.

    :return: tuple of buttons ``(run_btn, pause_btn, step_btn, reset_btn)``.
    """
    run_btn = mo.ui.run_button(label="▶ Run")
    pause_btn = mo.ui.run_button(label="⏸ Pause")
    step_btn = mo.ui.run_button(label="⏭ Step")
    reset_btn = mo.ui.run_button(label="⏹ Reset")
    return run_btn, pause_btn, step_btn, reset_btn


def init_refresh(is_running, refresh_interval, set_refresh_interval):
    """Build the auto-refresh speed selector.

    The widget is reconstructed whenever ``is_running`` toggles:

    * running -> ``default_interval`` = saved interval (timer ticks)
    * paused  -> ``default_interval`` = ``None`` (shows "Off", no ticks)

    The user's chosen speed is preserved across pause/resume by writing it
    back into ``set_refresh_interval`` on every change.

    :param is_running: current running state (bool).
    :param refresh_interval: saved interval string, e.g. ``"0.5s"``.
    :param set_refresh_interval: setter to persist the user's chosen interval.
    """

    # keep track of previously selected value
    def _remember_interval(value):
        # value is like "0.5s (3)" — strip the tick counter to get the interval.
        if value:
            interval = value.split(" ")[0]
            if interval in REFRESH_INTERVAL_OPTIONS:
                set_refresh_interval(interval)

    return mo.ui.refresh(
        default_interval=refresh_interval if is_running else None,
        options=REFRESH_INTERVAL_OPTIONS,
        on_change=_remember_interval,
    )
