from simulatingrisk.hawkdovemulti.batch_run import run_hawkdovemulti_model
from simulatingrisk.hawkdovemulti.model import DataCollectionSchedule


def test_run_hawkdovemulti_model_no_duplicate_final_row():
    # regression: in ALL mode, the batch runner used to call
    # model.collect_data() unconditionally after the run loop, which
    # duplicated the final row (data for the last step was already
    # collected inside step()). ensure the last row is not duplicated.
    max_steps = 10
    args = (
        0,  # run_id
        0,  # iteration
        {"grid_size": 3, "risk_adjustment": None},
        max_steps,
        DataCollectionSchedule.ALL,
        False,  # collect_agent_data
    )
    model_data, _ = run_hawkdovemulti_model(args)
    # ALL mode collects on every step; batch loop runs while schedule.steps
    # <= max_steps, so a small non-converging model produces max_steps + 1
    # rows. crucially, no two consecutive rows should be identical duplicates.
    assert len(model_data) >= 2
    # spot-check: last two rows should differ (no duplicate final row)
    assert model_data[-1] != model_data[-2]


def test_run_hawkdovemulti_model_end_mode_has_final_row():
    # END mode: model only collects when it stops running. if the loop
    # exits because max_steps was reached without convergence, the batch
    # runner must force a final collect so the output isn't empty.
    max_steps = 10
    args = (
        0,
        0,
        {"grid_size": 3, "risk_adjustment": None},
        max_steps,
        DataCollectionSchedule.END,
        False,
    )
    model_data, _ = run_hawkdovemulti_model(args)
    # exactly one row for END mode
    assert len(model_data) == 1
