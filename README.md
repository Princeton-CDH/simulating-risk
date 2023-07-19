# Simulating Risk

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
