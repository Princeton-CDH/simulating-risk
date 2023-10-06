import csv
import os
from datetime import date
from unittest.mock import patch

from simulatingrisk.batch_run import (
    riskybet_batch_run,
    riskyfood_batch_run,
    save_results,
)
from simulatingrisk.risky_bet.model import RiskyBetModel
from simulatingrisk.risky_food.model import RiskyFoodModel


# patch mesa.batch_run in context of local batch run script
@patch("simulatingrisk.batch_run.batch_run")
@patch("simulatingrisk.batch_run.save_results")
def test_riskybet_batch_run(mock_save_results, mock_batch_run):
    # assert mesa batch run is called as expected
    # FIXME: this test is too brittle,
    # as written has to be updated everytime we change batch run options
    riskybet_batch_run()
    mock_batch_run.assert_called_with(
        RiskyBetModel,
        parameters={
            "grid_size": 30,  # [10, 20, 30],  # 100],
            # "grid_size": [10, 20, 30],  # 100],
            # "risk_adjustment": ["adopt", "average"],
            "risk_adjustment": "adopt",
        },
        iterations=5,
        max_steps=3000,
        number_processes=1,  # set None to use all available; set 1 for jupyter
        data_collection_period=1,
        display_progress=True,
    )
    mock_save_results.assert_called_with("riskybet", mock_batch_run.return_value)


# patch mesa.batch_run in context of local batch run script
@patch("simulatingrisk.batch_run.batch_run")
@patch("simulatingrisk.batch_run.save_results")
def test_riskyfood_batch_run(mock_save_results, mock_batch_run):
    # assert mesa batch run is called as expected
    riskyfood_batch_run()
    mock_batch_run.assert_called_with(
        RiskyFoodModel,
        parameters={"n": 110, "mode": "types"},
        iterations=5,
        max_steps=1000,
        number_processes=1,  # set None to use all available; set 1 for jupyter
        data_collection_period=1,
        display_progress=True,
    )
    mock_save_results.assert_called_with("riskyfood", mock_batch_run.return_value)


def test_save_results(capsys, tmpdir):
    # output is saved to current working directory;
    # change working directory to tmpdir
    os.chdir(tmpdir)
    mock_data = [{"a": 1, "b": 2}, {"a": 10, "b": 20, "c": 3}]
    outfile = save_results("simulationfoo", mock_data)
    # filename includes simulation name, date/time and csv extension
    assert outfile.startswith("simulationfoo_")
    assert date.today().isoformat() in outfile
    assert outfile.endswith(".csv")

    captured = capsys.readouterr()
    assert captured.out == ("Saving data collection results to: %s\n" % outfile)

    with open(outfile) as testcsv:
        csvreader = csv.DictReader(testcsv)
        rows = list(csvreader)
        # should include keys from last rof of data even if not present in first
        assert set(rows[0].keys()) == {"a", "b", "c"}
        # spot check some data
        assert rows[0]["a"] == "1"  # string because read from file
        assert rows[1]["b"] == "20"
