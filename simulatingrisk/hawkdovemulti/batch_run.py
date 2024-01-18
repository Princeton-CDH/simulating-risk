#!/usr/bin/env python

import argparse
import csv
from datetime import datetime
import multiprocessing
import os

from tqdm.auto import tqdm

from mesa.batchrunner import _make_model_kwargs, _collect_data

from simulatingrisk.hawkdovemulti.model import HawkDoveMultipleRiskModel


neighborhood_sizes = list(HawkDoveMultipleRiskModel.neighborhood_sizes)

# combination of parameters we want to run
params = {
    "grid_size": [10, 25, 50],  # 100],
    "risk_adjustment": ["adopt", "average"],
    "play_neighborhood": neighborhood_sizes,
    "observed_neighborhood": neighborhood_sizes,
    "adjust_neighborhood": neighborhood_sizes,
    "hawk_odds": [0.5, 0.25, 0.75],
    "adjust_every": [2, 10, 20],
    "risk_distribution": HawkDoveMultipleRiskModel.risk_distribution_options,
    "adjust_payoff": HawkDoveMultipleRiskModel.supported_adjust_payoffs,
    # random?
}


# method for multiproc running model with a set of params
def run_hawkdovemulti_model(args):
    run_id, iteration, params, max_steps = args
    # simplified model runner adapted from mesa batch run code

    model = HawkDoveMultipleRiskModel(**params)
    while model.running and model.schedule.steps <= max_steps:
        model.step()

    # collect data for the last step
    step = model.schedule.steps - 1

    model_data, all_agents_data = _collect_data(model, step)

    # combine run id, step, and params, with collected model data
    run_data = {"RunId": run_id, "iteration": iteration, "Step": step}
    run_data.update(params)
    run_data.update(model_data)

    agent_data = [
        {
            "RunId": run_id,
            "iteration": iteration,
            "Step": step,
            **agent_data,
        }
        for agent_data in all_agents_data
    ]

    return run_data, agent_data


def batch_run(
    params, iterations, number_processes, max_steps, progressbar, file_prefix=""
):
    param_combinations = _make_model_kwargs(params)
    total_param_combinations = len(param_combinations)
    total_runs = total_param_combinations * iterations
    print(
        f"{total_param_combinations} parameter combinations, "
        + f"{iterations} iteration{'s' if iterations != 1 else ''}, "
        + f"{total_runs} total runs"
    )

    # create a list of all the parameters to run, with run id and iteration
    runs_list = []
    run_id = 0
    for params in param_combinations:
        for iteration in range(iterations):
            runs_list.append((run_id, iteration, params, max_steps))
            run_id += 1

    # collect data in a directory for this model
    data_dir = os.path.join("data", "hawkdovemulti")
    os.makedirs(data_dir, exist_ok=True)
    datestr = datetime.today().isoformat().replace(".", "_").replace(":", "")
    model_output_filename = os.path.join(data_dir, f"{file_prefix}{datestr}_model.csv")
    agent_output_filename = os.path.join(data_dir, f"{file_prefix}{datestr}_agent.csv")
    print(
        "Saving data collection results to:\n  %s\n  %s"
        % (model_output_filename, agent_output_filename)
    )
    # open output files so data can be written as it is generated
    with open(model_output_filename, "w", newline="") as model_output_file, open(
        agent_output_filename, "w", newline=""
    ) as agent_output_file:
        model_dict_writer = None
        agent_dict_writer = None

        # adapted from mesa batch run code
        with tqdm(total=total_runs, disable=not progressbar) as pbar:
            with multiprocessing.Pool(number_processes) as pool:
                for model_data, agent_data in pool.imap_unordered(
                    run_hawkdovemulti_model, runs_list
                ):
                    # initialize dictwriter and start csv after the first batch
                    if model_dict_writer is None:
                        # get field names from first entry
                        model_dict_writer = csv.DictWriter(
                            model_output_file, model_data.keys()
                        )
                        model_dict_writer.writeheader()

                    model_dict_writer.writerow(model_data)

                    if agent_dict_writer is None:
                        # get field names from first entry
                        agent_dict_writer = csv.DictWriter(
                            agent_output_file, agent_data[0].keys()
                        )
                        agent_dict_writer.writeheader()

                    agent_dict_writer.writerows(agent_data)

                    pbar.update()


def main():
    parser = argparse.ArgumentParser(
        prog="hawk/dove batch_run",
        description="Batch run for hawk/dove multi risk attitude simulation",
    )
    parser.add_argument(
        "-i",
        "--iterations",
        type=int,
        help="Number of iterations to run for each set of parameters "
        + "(default: %(default)s)",
        default=100,
    )
    parser.add_argument(
        "-m",
        "--max-steps",
        help="Maximum steps to run simulations if they have not already "
        + "converged (default: %(default)s)",
        default=125,  # typically converges quickly, around step 60 without randomness
        type=int,
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        help="Number of processes to use (default: all available CPUs)",
        default=None,
    )
    parser.add_argument(
        "--progress",
        help="Display progress bar (default: %(default)s)",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--file-prefix",
        help="Prefix for data filenames",
    )
    # do we need an option to configure output dir?

    args = parser.parse_args()
    batch_run(
        params,
        args.iterations,
        args.processes,
        args.max_steps,
        args.progress,
        args.file_prefix,
    )


if __name__ == "__main__":
    main()
