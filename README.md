# Simulating Risk

## Development instructions

Initial setup and installation:

- *Recommmended*: create and activate a Python 3.9 virtualenv:
```sh
python3 -m venv simrisk
source simrisk/bin/activate
```
- Install python dependencies::
```sh
pip install -r requirements/dev.txt
```

### Install pre-commit hooks

Install pre-commit hooks (currently [black](https://github.com/psf/black) and [isort](https://pycqa.github.io/isort/)):
```sh
pre-commit install
```

Use Mesa runserver to run the prototype stag hunt model locally:
```sh
mesa runserver stag_hunt
```

