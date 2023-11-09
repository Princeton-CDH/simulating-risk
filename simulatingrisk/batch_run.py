#!/usr/bin/env python

import argparse
import csv
from datetime import datetime

from mesa import batch_run

from simulatingrisk.hawkdove.model import HawkDoveSingleRiskModel
from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel
from simulatingrisk.risky_bet.model import RiskyBetModel
from simulatingrisk.risky_food.model import RiskyFoodModel


def riskybet_batch_run(args=None):
    results = batch_run(
        RiskyBetModel,
        parameters={
            "grid_size": 30,  # [20, 30],  # 100],
            # "risk_adjustment": ["adopt", "average"],
            "risk_adjustment": "adopt",
        },
        iterations=5,
        # TODO: vary how often they update strategy
        # every 100, every 1 round?
        max_steps=3000,  # at least 1000, maybe more to see where it converges
        # try 10k to see
        # add logic on the model to stop if risk levels converge to 90% in one bin
        number_processes=1,  # set None to use all available; set 1 for jupyter
        data_collection_period=1,
        display_progress=True,
    )
    # returns a list of dictionaries from data collection across all runs
    save_results("riskybet", results)


def riskyfood_batch_run(args=None):
    results = batch_run(
        RiskyFoodModel,
        # only parameter to this one currently is number of agents
        parameters={"n": 110, "mode": "types"},
        iterations=5,  # this one is faster, could run more iterations
        max_steps=1000,
        number_processes=1,  # set None to use all available; set 1 for jupyter
        data_collection_period=1,
        display_progress=True,
    )
    save_results("riskyfood", results)


def hawkdove_singlerisk_batch_run(args):
    # params are:
    # grid_size,
    # include_diagonals=True,
    # agent_risk_level=None,
    # hawk_odds=0.5,

    params = {
        "grid_size": 20,
        "agent_risk_level": [0, 1, 2, 3, 4, 5, 6, 7, 8],
    }
    iterations = 1

    results = batch_run(
        HawkDoveSingleRiskModel,
        # when including diagonals, risk levels go from 0 to 8;
        # probably do not need to include the extremes for this analysis
        parameters=params,
        iterations=iterations,
        number_processes=1,
        data_collection_period=1,
        display_progress=True,
        max_steps=200,  # converges very quickly, so don't run 1000 times
    )
    # include the mode in the output filename
    save_results("hawkdove_single", results)


def hawkdove_multiplerisk_batch_run(args):
    params = {
        "grid_size": 10,
        "risk_adjustment": "adopt",  # run adopt only for now
    }
    iterations = 100
    results = batch_run(
        HawkDoveMultipleRiskModel,
        parameters=params,
        iterations=iterations,
        number_processes=1,
        data_collection_period=1,
        display_progress=True,
        max_steps=250,  # converges fairly quickly, don't run 1000 times
    )
    # include the mode in the output filename
    save_results("hawkdove_multiple", results)


def save_results(simulation, results):
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

    return output_filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="simulatingrisk batch_run",
        description="Run simulations in batch mode and save collected data",
    )
    # use subcommands so we can add model-specific options
    subparsers = parser.add_subparsers(help="Help for model-specific options")
    riskybet_parser = subparsers.add_parser("riskybet")
    riskybet_parser.set_defaults(func=riskybet_batch_run)
    riskyfood_parser = subparsers.add_parser("riskyfood")
    riskyfood_parser.set_defaults(func=riskyfood_batch_run)
    hawkdove_parser = subparsers.add_parser("hawkdove-single")
    # will any subparser arguments be needed in future?
    # hawkdove_parser.add_argument(
    #     "-r",
    #     "--risk-attitudes",
    #     choices=["single", "variable"],
    #     help="Mode for initializing agent risk attitudes",
    # )
    hawkdove_parser.set_defaults(func=hawkdove_singlerisk_batch_run)
    hawkdove_multi_parser = subparsers.add_parser("hawkdove-multi")
    hawkdove_multi_parser.set_defaults(func=hawkdove_multiplerisk_batch_run)

    args = parser.parse_args()
    # run appropriate function based on the selected subcommand
    # if a subcommand is not specified, no function is set
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        exit(-1)
