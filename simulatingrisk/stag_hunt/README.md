# Stag Hunt Simulation

## Summary

This is a preliminary, incomplete implementation of the Stag Hunt game, drawing on Skyrms' _The stag hunt and the evolution of social structure_ (2004).

With the current implementation and payoff scheme, it converges to everyone hunting stag fairly quickly, and is probably not very interesting; but it may useful as a reference with mesa simulations, or for further refinement and experimentation.

## Running the simulation

- Install python dependencies as described in the main project readme (requires mesa)
- To run from the main `simulating-risk` project directory: 
	- Configure python to include the current directory in import path; 
	  for C-based shells, run `setenv PYTHONPATH .` ; for bash, run `export $PYTHONPATH=.`
	- To run interactively with mesa runserver: `mesa runserver simulatingrisk/stag_hunt/`
