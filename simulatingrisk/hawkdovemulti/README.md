# Hawk-Dove with multiple risk attitudes

This is a variation of the [Hawk/Dove game with risk attitudes](../hawkdove/).
This version adds multiple risk attitudes, with options for updating
risk attitudes periodically based on comparing success of neighboring agents.

The basic mechanics of the game are the same. This model adds options
for agent risk adjustment (none, adopt, average) and period of risk
adjustment (by default, every ten rounds). The payoff used to compare
agents when adjusting risk attitudes can either be recent (since the
last adjustment round) or total points for the whole game. The
adjustment neighborhood, or which neighboring agents are considered
when adjusting risk attitudes, can be configured to 4, 8, or 24.

Initial risk attitudes are set by the model. Risk distribution can
be configured to use a normal distribution, uniform (random), bimodal,
skewed left, or skewed right.

Like the base hawk/dove risk attitude game, there is also a
configuration to add some chance of agents playing hawk/dove randomly
instead of choosing based on the rules of the game.

## Convergence

The model is configured to stop automatically when it has stabilized.

Model and agent data collection reports on whether agents updated their
risk level in the last adjustment round, and model data collection
includes a status of "running" or "converged".

### With Adjustment

When adjustment is enabled (adopt / average), convergence is checked
after the simulation has run for a minimum of 50 rounds.  The simulation
is considered stable when individual agents are no longer adjusting risk attitudes,
or when the number of agents in each risk attitude are relatively stable
(e.g., agents are swapping risk attitudes but the overall total for each
category is stable).

Convergence is reached when an adjustment round occurs and _either_:

-  _zero_ agents adjust their risk attitude
- the total changes of agents per risk attitudes is less than 7% of the population size

### Without Adjustment

If adjustment is not enabled, convergence logic falls back to the
implementation of the hawk/dove single-risk attitude simulation. In this case,
convergence is based on a stable rolling % average of agents playing hawk.


## Batch running

This module includes a custom batch run script to run the simulation and
collect data across a large combination of parameters and generate data
files with collected model and agent data.

To run the script locally from the root project directory:
```sh
simulatingrisk/hawkdovemulti/batch_run.py
```
Use `-h` or `--help` to see options.

If this project has been installed with pip or similar, the script is
available as `simrisk-hawkdovemulti-batchrun`.

To run the batch run script on an HPC cluster:

- Create a conda environment and install dependencies and this project.
  (Major mesa dependencies available with conda are installed first as
  conda packages)

```sh
module load anaconda3/2023.9
conda create --name simrisk pandas networkx matplotlib numpy tqdm click
conda activate simrisk
pip install git+https://github.com/Princeton-CDH/simulating-risk.git@hawkdove-batchrun
```
For convenience, an example [slurm batch script](simrisk_batch.slurm) is
included for running the batch run script (some portions are
specific to Princeton's Research Computing HPC environment.)

- Customize the slurm batch script as desired, copy it to the cluster, and submit
the job: `sbatch simrisk_batch.slurm`

By default, the batch run script will use all available processors, and will
create model and agent data files under a `data/hawkdovemulti/` directory
relative to the working directory where the script is called.




