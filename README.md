# Simulating Risk

The code in this repository is associated with the CDH project [Simulating risk, risking simulations](https://cdh.princeton.edu/projects/simulating-risk/).

Simulations are implemented with [Mesa](https://mesa.readthedocs.io/en/stable/), using Agent Based Modeling to explore risk attitudes within populations.

Across simulations, we define agents with risk attitudes tracked via a numeric `r` or `risk_level` 0.0 - 1.0, where `r` is that agent's minimum acceptable risk level for taking the risky bet. When the probability 'p' of the risky bet paying off is greater than an agent's 'r', that agent will take the bet. An agent with `r=1` will always take the safe option (no risk is acceptable); an agent with `r=0` will always take the risky choice (any risk is acceptable). Notice that the agent is never indifferent; allowing indifference would require introducing a tie-breaking rule, which would be a further parameter.

When the risky bet might be better or worse than the safe bet by the same amount (for example, the risky bet yields 3 or 1 and the safe bet yields 2), an agent who maximizes expected utility will prefer the risky bet when p > 0.5 and will prefer the safe bet when 'p < 0.5'; and they will be indifferent between the risky bet and the safe bet. Thus, r = 0.5 corresponds to expected utility maximization except in the case in which the probability is exactly 0.5 (or, we might say, a point epsilon units to the left of 0.5, where epsilon is smaller than the fineness of our random number generator, corresponds to expected utility maximization). These complications make no difference in practice, so we can simply say that r = 0.5 corresponds to expected utility maximization.



```mermaid
---
title: risk attitude / risk level (for probabilistic choices)
---
flowchart LR
    r0["<b>0.0</b>
always takes risky choice
(any risk is acceptable)"]
    reu["<b>0.5</b>
risk neutral
(expected utility maximizer)"]
    r1["<b>1.0</b>
always takes safe choice
(no risk is acceptable)"]
    r0 ---|risk seeking|reu---|risk averse|r1
```


## Development instructions

Initial setup and installation:

- *Recommmended*: create and activate a Python 3.9 virtualenv:
```sh
python3 -m venv simrisk
source simrisk/bin/activate
```
- Install the package, dependencies, and development dependencies:
```sh
pip install -e .
pip install -e ".[dev]"
```

### Running the simulations

- Simulations can be run interactively with mesa runserver by specifying
  the path to the model, e.g. `mesa runserver simulatingrisk/risky_bet/`
  Refer to the readme for each model for more details.
- Simulations can be run in batches to aggregate data across multiple
  runs and different parameters. For example,
  `./simulatingrisk/batch_run.py riskyfood`


### Install pre-commit hooks

Install pre-commit hooks (currently [black](https://github.com/psf/black) and [ruff](https://beta.ruff.rs/docs/)):

```sh
pre-commit install
```
