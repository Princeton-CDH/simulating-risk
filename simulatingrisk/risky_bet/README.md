# Risky Bet Simulation

## Summary

Game: agents start with random fixed risk attitudes (similar to the
risky food simulation), and decide whether or not to make a risky bet.
Every ten rounds, agents adjust their risk attitude based on the
relative wealth of their neighbors.

SETUP:
- Fixed agents on an NxN grid with random risk attitudes
- Every agent starts with $1000 initial wealth

EACH ROUND:
- The model selects a probability `p` of the RISKY bet paying off
- Each agent has a risk attitude `r`, and will take the RISKY bet if `p` > `r`
- The model flips a coin with bias `p` to determine whether the RISKY bet paid off.
- For agents who choose the SAFE option (no bet), money is unchanged; for agents who took the RISKY bet, money is either multiplied by 1.5 (if the bet paid off) or 0.5 (if it didn't).
END ROUND

EVERY 10 ROUNDS, adjust risk attitudes:
- Each agent looks at their neighbors (4).
- If anyone has more money, either adopt their risk attitude or average between current risk attitude and theirs (configurable via a model intialization parameter).
- Reset wealth back to the initial value ($1000).

Collect data to track how the distribution of risk attitudes changes over time.
Visualize a grid using a divergent color spectrum with for risk levels; use
eleven bins, with bins for 0 - 0.05 and 0.95 - 1.0, since risk = 0, 0.5, and 1
are all special cases we want clearly captured.

## Running the simulation

- Install python dependencies as described in the main project readme (requires mesa)
- Use the main `simulating-risk` project directory as your working directory
- To run with `mesa runserver` from the command line:
  - Configure python to include the current directory in import path;
	for C-based shells, run `setenv PYTHONPATH .` ; for bash, run `export $PYTHONPATH=.`
  - To run interactively with mesa runserver: `mesa runserver simulatingrisk/risky_bet/`
- To run with `solara` from the commandline:
   - `solara run --host localhost simulatingrisk/risky_bet/app.py`
- To run in a Jupyter notebook or Colab, import the `JupyterViz` page object:
```python
from simulatingrisk.risky_bet.app import page
page
```
