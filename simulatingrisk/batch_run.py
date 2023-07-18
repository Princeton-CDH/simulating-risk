import csv
from datetime import datetime

from mesa import batch_run

from simulatingrisk.risky_bet.model import RiskyBetModel


def riskybet_batch_run():
    results = batch_run(
        RiskyBetModel,
        parameters={
            "grid_size": [10, 20, 30],  # 100],
            "risk_adjustment": ["adopt", "average"],
        },
        iterations=5,
        max_steps=100,
        number_processes=1,  # set None to use all available; set 1 for jypeter
        data_collection_period=1,
        display_progress=True,
    )
    # returns a list of dictionaries that can be opened with pandas;
    # save as csv for external analysis
    # - use datetime to distinguish this run, but make nicer for filename
    datestr = datetime.today().isoformat().replace(".", "_").replace(":", "")
    output_filename = "riskybet_%s.csv" % datestr
    print("Saving data collection results to: %s" % output_filename)
    # get field names from last entry, since first entry is for the model
    # and doesn't include agent-level data
    fields = results[-1].keys()
    with open(output_filename, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, fields)
        dict_writer.writeheader()
        dict_writer.writerows(results)


if __name__ == "__main__":
    riskybet_batch_run()
