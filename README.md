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

### Install pre-commit hooks

Install pre-commit hooks (currently [black](https://github.com/psf/black) and [ruff](https://beta.ruff.rs/docs/)):

```sh
pre-commit install
```
