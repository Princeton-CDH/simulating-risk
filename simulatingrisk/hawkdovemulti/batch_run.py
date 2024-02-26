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
    "default": {
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
    },
    # specific scenarios to allow paired statistical tests
    "risk_adjust": {
        # ary risk adjustment
        "risk_adjustment": ["adopt", "average"],
        # use model defaults; grid size must be specified
        "grid_size": 10,  # 25,
    },
    "payoff": {
        "adjust_payoff": HawkDoveMultipleRiskModel.supported_adjust_payoffs,
        # use model defaults; grid size must be specified
        "grid_size": 25,
    },
    "distribution": {
        "risk_distribution": HawkDoveMultipleRiskModel.risk_distribution_options,
        "risk_adjustment": "average",
        # use model defaults; grid size must be specified
        "grid_size": 10,
    },
}


# method for multiproc running model with a set of params
def run_hawkdovemulti_model(args):
    run_id, iteration, params, max_steps = args
    # simplified model runner adapted from mesa batch run code

    model = HawkDoveMultipleRiskModel(**params)
    while model.running and model.schedule.steps <= max_steps:
        try:
            model.step()
        # by default, signals propagate to all processes
        # take advantage of that to exit and save results
        except KeyboardInterrupt:
            # if we get a ctrl-c / keyboard interrupt, stop looping
            # and finish data collection to report on whatever was completed
            break

    # collect data for the last step
    # (scheduler is 1-based index but data collection is 0-based)
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
    params,
    iterations,
    number_processes,
    max_steps,
    progressbar,
    collect_agent_data,
    file_prefix,
    max_runs,
    param_choice,
):
    run_params = params.get(param_choice)

    param_combinations = _make_model_kwargs(run_params)
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

    # if maximum runs is specified, truncate the list of run arguments
    if max_runs:
        runs_list = runs_list[:max_runs]

    # collect data in a directory for this model
    data_dir = os.path.join("data", "hawkdovemulti")
    os.makedirs(data_dir, exist_ok=True)
    datestr = datetime.today().isoformat().replace(".", "_").replace(":", "")
    model_output_filename = os.path.join(data_dir, f"{file_prefix}{datestr}_model.csv")
    if collect_agent_data:
        agent_output_filename = os.path.join(
            data_dir, f"{file_prefix}{datestr}_agent.csv"
        )

    message = f"Saving data collection results to:\n  {model_output_filename}"
    if collect_agent_data:
        message += f"\n  {agent_output_filename}"
    print(message)

    # open output files so data can be written as it is generated
    with open(model_output_filename, "w", newline="") as model_output_file:
        if collect_agent_data:
            agent_output_file = open(agent_output_filename, "w", newline="")

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

                    if collect_agent_data:
                        if agent_dict_writer is None:
                            # get field names from first entry
                            agent_dict_writer = csv.DictWriter(
                                agent_output_file, agent_data[0].keys()
                            )
                            agent_dict_writer.writeheader()

                        agent_dict_writer.writerows(agent_data)

                    pbar.update()

        if collect_agent_data:
            agent_output_file.close()


def main():
    parser = argparse.ArgumentParser(
        prog="hawk/dove batch_run",
        description="Batch run for hawk/dove multiple risk attitude simulation.",
        epilog="""Data files will be created in data/hawkdovemulti/
        relative to current path.""",
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
        default=1000,  # new convergence logic seems to converge around 400
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
        help="Display progress bar",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--agent-data",
        help="Store agent data",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--file-prefix",
        help="Prefix for data filenames (no prefix by default)",
        default="",
    )
    parser.add_argument(
        "--max-runs",
        help="Stop after the specified number of runs "
        + "(for development/troubleshooting)",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--params",
        help="Run a specific set of parameters",
        choices=params.keys(),
        default="default",
    )

    args = parser.parse_args()
    batch_run(
        params,
        args.iterations,
        args.processes,
        args.max_steps,
        args.progress,
        args.agent_data,
        args.file_prefix,
        args.max_runs,
        args.params,
    )


if __name__ == "__main__":
    main()
