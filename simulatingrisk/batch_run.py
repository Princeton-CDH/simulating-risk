#!/usr/bin/env python

import argparse
import csv
from datetime import datetime

from mesa import batch_run

from simulatingrisk.risky_bet.model import RiskyBetModel
from simulatingrisk.risky_food.model import RiskyFoodModel


def riskybet_batch_run():
    results = batch_run(
        RiskyBetModel,
        parameters={
            "grid_size": [10, 20, 30],  # 100],
            "risk_adjustment": ["adopt", "average"],
        },
        iterations=5,
        max_steps=100,
        number_processes=1,  # set None to use all available; set 1 for jupyter
        data_collection_period=1,
        display_progress=True,
    )
    # returns a list of dictionaries from data collection across all runs
    return results


def riskyfood_batch_run():
    results = batch_run(
        RiskyFoodModel,
        # only parameter to this one currently is number of agents
        parameters={
            "n": 10,  # [10, 20, 30],  # 100],
        },
        iterations=5,
        max_steps=22,  # population gets too large after 25/26 rounds...
        number_processes=1,  # set None to use all available; set 1 for jupyter
        data_collection_period=1,
        display_progress=True,
    )
    return results


def save_results(simulation, data):
    # save as csv for external analysis
    # - use datetime to distinguish this run, but make nicer for filename
    datestr = datetime.today().isoformat().replace(".", "_").replace(":", "")
    output_filename = "%s_%s.csv" % (simulation, datestr)
    print("Saving data collection results to: %s" % output_filename)
    # get field names from last entry, since first entry is for the model
    # and doesn't include agent-level data
    fields = results[-1].keys()
    with open(output_filename, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, fields)
        dict_writer.writeheader()
        dict_writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="simulatingrisk batch_run",
        description="Run simulations in batch mode and save collected data",
    )
    parser.add_argument("simulation", choices=["riskybet", "riskyfood"])
    args = parser.parse_args()

    if args.simulation == "riskybet":
        results = riskybet_batch_run()
    elif args.simulation == "riskyfood":
        results = riskyfood_batch_run()

    save_results(args.simulation, results)
