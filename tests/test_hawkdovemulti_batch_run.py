from simulatingrisk.hawkdovemulti.batch_run import run_hawkdovemulti_model
from simulatingrisk.hawkdovemulti.model import DataCollectionSchedule


def test_run_hawkdovemulti_model_output_columns_end():
    # rows must be self-describing: RunId, iteration, Step, and every
    # input parameter should appear as columns, alongside the model
    # data reporters.
    max_steps = 10
    params = {
        "grid_size": 3,
        "risk_adjustment": "adopt",
        "hawk_odds": 0.4,
        "adjust_every": 5,
    }
    args = (
        7,  # run_id
        2,  # iteration
        params,
        max_steps,
        DataCollectionSchedule.END,
        False,
    )
    model_data, _ = run_hawkdovemulti_model(args)
    assert len(model_data) == 1
    row = model_data[0]
    # identifying columns
    assert row["RunId"] == 7
    assert row["iteration"] == 2
    # Step should be the final step index reached, not 0
    assert (
        row["Step"] == max_steps
    )  # loop ran max_steps + 1 steps, index of last is max_steps
    # every input param should be echoed as a column
    for key, value in params.items():
        assert row[key] == value
    # at least one model reporter should be present
    assert "percent_hawk" in row
    # data-collection knobs should NOT leak into the row as spurious columns
    assert "data_collection_schedule" not in row
    assert "collect_agent_data" not in row


def test_run_hawkdovemulti_model_step_column_all():
    # in ALL mode, one row per step; Step should be a 0-based step index
    max_steps = 5
    args = (
        0,
        0,
        {"grid_size": 3, "risk_adjustment": None},
        max_steps,
        DataCollectionSchedule.ALL,
        False,
    )
    model_data, _ = run_hawkdovemulti_model(args)
    step_values = [row["Step"] for row in model_data]
    # steps should start at 0 and be strictly increasing by 1
    assert step_values == list(range(len(step_values)))


def test_run_hawkdovemulti_model_step_column_adjust():
    # in ADJUST mode, rows are collected on adjustment rounds only;
    # Step for row i should be (i+1)*adjust_every - 1.
    adjust_every = 5
    max_steps = 20
    args = (
        0,
        0,
        {
            "grid_size": 3,
            "risk_adjustment": "adopt",
            "adjust_every": adjust_every,
        },
        max_steps,
        DataCollectionSchedule.ADJUST,
        False,
    )
    model_data, _ = run_hawkdovemulti_model(args)
    step_values = [row["Step"] for row in model_data]
    expected = [(i + 1) * adjust_every - 1 for i in range(len(step_values))]
    assert step_values == expected


def test_run_hawkdovemulti_model_agent_data_columns():
    # agent data output should also include RunId, iteration, and every
    # param as columns; Step should be 0-based to match model output.
    max_steps = 3
    params = {"grid_size": 3, "risk_adjustment": None, "hawk_odds": 0.6}
    args = (
        4,
        1,
        params,
        max_steps,
        DataCollectionSchedule.ALL,
        True,  # collect_agent_data
    )
    _, agent_data = run_hawkdovemulti_model(args)
    assert agent_data is not None
    assert len(agent_data) > 0
    row = agent_data[0]
    assert row["RunId"] == 4
    assert row["iteration"] == 1
    # params not included in agent data
    for key in params.keys():
        assert key not in row

    # Step should be 0-based
    step_values = {r["Step"] for r in agent_data}
    assert min(step_values) == 0


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
