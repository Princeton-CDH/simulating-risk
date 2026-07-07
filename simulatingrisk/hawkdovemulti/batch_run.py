#!/usr/bin/env python

import argparse
import csv
import multiprocessing
import os
from datetime import datetime
from pathlib import Path

from mesa.batchrunner import _make_model_kwargs
from tqdm.auto import tqdm

from simulatingrisk.hawkdovemulti.model import (
    DataCollectionSchedule,
    HawkDoveMultipleRiskModel,
)

neighborhood_sizes = list(HawkDoveMultipleRiskModel.neighborhood_sizes)

# NOTE: it's better to be explicit about parameters
# instead of relying on model defaults, because
# parameters specified here are included in data exports


# combination of parameters we want to run
params = {
    "default": {
        "grid_size": [5, 10, 25],  # , 50],  # 100],
        "risk_adjustment": ["adopt", "average"],
        "play_neighborhood": neighborhood_sizes,
        "observed_neighborhood": neighborhood_sizes,
        "adjust_neighborhood": neighborhood_sizes,
        "hawk_odds": [0.5, 0.25, 0.75],
        "adjust_every": [2, 10, 20],
        "risk_distribution": HawkDoveMultipleRiskModel.risk_distribution_options,
        "adjust_payoff": HawkDoveMultipleRiskModel.supported_adjust_payoffs,
        "random_play_odds": [0, 0.01, 0.1],
        "include_endpoints": [True, False],
    },
    # specific scenarios to allow paired statistical tests
    "risk_adjust": {
        # any risk adjustment
        "risk_adjustment": ["adopt", "average"],
        "risk_distribution": "uniform",
        # use model defaults; grid size must be specified
        "grid_size": [5, 10, 25],
    },
    "payoff": {
        "adjust_payoff": HawkDoveMultipleRiskModel.supported_adjust_payoffs,
        "risk_distribution": "uniform",
        # use model defaults; grid size must be specified
        "grid_size": 25,
    },
    "risk_distribution": {
        "risk_distribution": HawkDoveMultipleRiskModel.risk_distribution_options,
        # adopt tends to converge faster; LB also says it's more interesting & simpler
        "risk_adjustment": "adopt",
        # use model defaults; grid size must be specified
        "grid_size": 10,
    },
    "no_adjustment": {
        # no risk adjustment
        "risk_adjustment": None,
        "risk_distribution": HawkDoveMultipleRiskModel.risk_distribution_options,
        "play_neighborhood": neighborhood_sizes,
        "observed_neighborhood": neighborhood_sizes,
        # adjust payoff doesn't matter since we're not adjusting
        "grid_size": [5, 10, 25, 50],
        "hawk_odds": [0.5, 0.25, 0.75],
        "random_play_odds": [0, 0.01, 0.1],
        "include_endpoints": [True, False],
    },
}


# method for multiproc running model with a set of params
def run_hawkdovemulti_model(args) -> tuple[list[dict], list[dict] | None]:
    (
        run_id,
        iteration,
        params,
        max_steps,
        data_collection_schedule,
        collect_agent_data,
    ) = args
    # simplified model runner adapted from mesa batch run code
    # returns a tuple of model data, agent data (or None if not collecting agent data)
    # data for each is returned as a list of dicts

    # initialize model with run parameters and data collection options
    model = HawkDoveMultipleRiskModel(
        **params,
        data_collection_schedule=data_collection_schedule,
        collect_agent_data=collect_agent_data,
    )
    while model.running and model.schedule.steps <= max_steps:
        try:
            model.step()
        # by default, signals propagate to all processes
        # take advantage of that to exit and save results
        except KeyboardInterrupt:
            # if we get a ctrl-c / keyboard interrupt, stop looping
            # and finish data collection to report on whatever was completed
            break

    # data collection schedule is now handled in the model, so we don't
    # collect model/agent data we don't need.
    #
    # For END mode, the model only collects when it stops running (converges);
    # if we stopped without converging, force a final collect for last round data.
    # (ADJUST mode should also include last round, whether or not it was an adjustment
    # round.)
    if data_collection_schedule is not DataCollectionSchedule.ALL and model.running:
        model.running = False
        model.collect_data()

    # convert all collected model data into a list of dicts (one per collected
    # step), tagging each row with run id, iteration, step number (tracked
    # by the model), and the model parameter values that produced it, so
    # rows are self-describing in the exported CSV.
    model_vars = model.datacollector.model_vars
    collected_steps = list(model.collected_steps)
    reporter_names = list(model_vars)
    model_data = [
        {
            "RunId": run_id,
            "iteration": iteration,
            "Step": collected_steps[i],
            **params,
            **{name: model_vars[name][i] for name in reporter_names},
        }
        for i in range(len(collected_steps))
    ]

    # optionally get all agent data
    agent_data = None
    if collect_agent_data:
        # _agent_records is a dict keyed by schedule.steps at collect time;
        # each value is a list of (step, agent_id, *reporter_values) tuples.
        # convert to a flat list of dicts. Step from mesa is 1-based
        # (schedule.steps at collect time); shift to 0-based to match
        # the model data output.
        agent_reporters = list(model.datacollector.agent_reporters)
        agent_data = [
            {
                "RunId": run_id,
                "iteration": iteration,
                "Step": step_key - 1,
                "AgentID": record[1],
                **dict(zip(agent_reporters, record[2:])),
            }
            for step_key, records in model.datacollector._agent_records.items()
            for record in records
        ]

    return model_data, agent_data


def batch_run(
    params: dict,
    iterations: int,
    number_processes: int,
    max_steps: int,
    progressbar: bool,
    file_prefix: str,
    max_runs: int,
    param_choice: str,
    data_collection_schedule: DataCollectionSchedule,
    collect_agent_data: bool,
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
            runs_list.append(
                (
                    run_id,
                    iteration,
                    params,
                    max_steps,
                    data_collection_schedule,
                    collect_agent_data,
                )
            )
            run_id += 1

    # if maximum runs is specified, truncate the list of run arguments
    if max_runs:
        runs_list = runs_list[:max_runs]

    # collect data in a subdirectory based on parameter
    # (no model subdir since we're only focusing on hawk/dove multiple risk model)
    data_dir = Path("data") / param_choice
    data_dir.mkdir(parents=True, exist_ok=True)
    datestr = datetime.today().isoformat().replace(".", "_").replace(":", "")
    model_output_filename = os.path.join(data_dir, f"{file_prefix}{datestr}_model.csv")
    message = f"Saving data collection results to:\n  {model_output_filename}"

    # optionally collect agent data
    agent_output_filename = None
    agent_output_file = None
    if collect_agent_data:
        agent_output_filename = os.path.join(
            data_dir, f"{file_prefix}{datestr}_agent.csv"
        )
        message += f"\n  {agent_output_filename}"
    print(message)

    # open output files so data can be written as it is generated
    with open(model_output_filename, "w", newline="") as model_output_file:
        if agent_output_filename:
            agent_output_file = open(agent_output_filename, "w", newline="")

        model_dict_writer = None
        agent_dict_writer = None

        # adapted from mesa batch run code
        # use maxtasksperchild to recycle worker processes
        # to release accumulated memory and reduce risk of out of memory problems
        interrupted = False
        with tqdm(total=total_runs, disable=not progressbar) as pbar:
            with multiprocessing.Pool(number_processes, maxtasksperchild=10) as pool:
                # iterate over results in a loop so we can specify a timeout
                # and handle keyboard interrupts cleanly.
                results_iter = pool.imap_unordered(run_hawkdovemulti_model, runs_list)
                try:
                    while True:
                        try:
                            model_data, agent_data = results_iter.next(timeout=3600)
                        except multiprocessing.TimeoutError:
                            print(
                                "\nTimeout error waiting for a simulation run to "
                                "complete; possible crash or OOM. Quitting."
                            )
                            break
                        except StopIteration:
                            break

                        # initialize dictwriter and start csv after the first batch
                        if model_dict_writer is None:
                            # get field names from first entry (assumes rows are consistent;
                            # must be enforced in model data collection)
                            model_dict_writer = csv.DictWriter(
                                model_output_file, model_data[0].keys()
                            )
                            model_dict_writer.writeheader()

                        model_dict_writer.writerows(model_data)
                        # flush after every batch so partial results survive
                        # an abrupt exit
                        model_output_file.flush()

                        if agent_output_file:
                            if agent_dict_writer is None:
                                # get field names from first entry
                                agent_dict_writer = csv.DictWriter(
                                    agent_output_file, agent_data[0].keys()
                                )
                                agent_dict_writer.writeheader()

                            agent_dict_writer.writerows(agent_data)
                            agent_output_file.flush()

                        pbar.update()
                except KeyboardInterrupt:
                    # on ctrl-c, terminate workers so we don't wait for
                    # in-flight tasks; partial results already written to
                    # disk (thanks to the flushes above) are preserved.
                    interrupted = True
                    print(
                        "\nKeyboard interrupt received; terminating worker pool "
                        "and finalizing output files."
                    )
                    pool.terminate()
                    pool.join()

        if agent_output_file:
            agent_output_file.close()

        if interrupted:
            print("Batch run interrupted; partial results saved.")


# map cli data collection options to data collection schedule enum
data_collection_opts = {
    "end": DataCollectionSchedule.END,
    "adjust": DataCollectionSchedule.ADJUST,
    "all": DataCollectionSchedule.ALL,
}


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
        help="Number of processes (default: all available CPUs, %(default)d)",
        default=os.cpu_count(),  # process_cpu_count in newer python versions
    )
    parser.add_argument(
        "--progress",
        help="Display progress bar",
        action=argparse.BooleanOptionalAction,
        default=True,
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
    parser.add_argument(
        "--collect-data",
        help="When and how often to collect model and agent data",
        choices=data_collection_opts.keys(),
        default="end",
    )
    parser.add_argument(
        "--agent-data",
        help="Store agent data",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    args = parser.parse_args()

    # convert command-line string arg to data collection value
    collect_data = data_collection_opts[args.collect_data]

    batch_run(
        params,
        args.iterations,
        args.processes,
        args.max_steps,
        args.progress,
        args.file_prefix,
        args.max_runs,
        args.params,
        collect_data,
        args.agent_data,
    )


if __name__ == "__main__":
    main()
