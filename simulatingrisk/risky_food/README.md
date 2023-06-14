# Risky Food Simulation

## Summary

Game: risky food source is 3 if **N**, 1 if **C**; safe source is 2

- **N**: non-contaminated 
- **C**: contaminated

Every agent gets a parameter `r` between 0 and 1.  [or DISCRETE: 8 buckets etc.]

EACH ROUND:
- Nature selects a probability `p` for **N**
- For each agent: if `r` > `p`, then they choose RISKY; else SAFE
- Nature flips a coin with bias `p` for **N**, and announces **N** or **C**
- If **N**: everyone who chose RISKY gets 3, everyone who chose SAFE gets 2
- If **C**: everyone who chose RISKY gets 1, everyone SAFE 2
- Reproduce in proportion to payoff
  - Either agent gets # of offspring = payoff [they replace–original “dies off”]
  - OR: take the total payoff for RISKYs over total for everyone, there are that proportion of RISKYs in the new population

END ROUND

SEE: We’ll see what are the risk attitudes that are replicated more and less over time

## Running the simulation

- Install python dependencies as described in the main project readme (requires mesa)
- To run from the main `simulating-risk` project directory: 
	- Configure python to include the current directory in import path; 
	  for C-based shells, run `setenv PYTHONPATH .` ; for bash, run `export $PYTHONPATH=.`
	- To run interactively with mesa runserver: `mesa runserver simulatingrisk/risky_food/`
