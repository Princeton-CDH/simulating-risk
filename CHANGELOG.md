# 1.2.0 - 2026-07-20

- Updated interactive ui logic to resize agent grid chart based on grid size; tested and optimized to go up to 72x72 with decreased refresh frequency.
- Updated analysis notebooks for current batch run data, adapting and expanding previous analysis. Written in marimo, and exported as static html to docs/analysis/
- Create `analysis_utils` module within non-adjusting notebooks, for shared functionality.
- Improved justfile logic for exporting app and notebooks to html docs.

# 1.1.0 - 2026-07-10

Updates to support the paper "Playing Risky Games."

Changes that affect both versions of the Hawk/Dove model:

- Revise default random play odds to 0.1 ; add to default batch run parameters
- Add boolean parameter to control whether to include extreme risk-attitudes 0 and 9 (`include_endpoints`, default is True)
- Add `include_endpoints` parameter to interactive simulation controls
- Update labels and legends in the interactive simulation and analysis notebooks to match language in the paper.
- Add a marimo notebook to serve as the interface for running the Hawk/Dove simulation interactively; supports export to html+wasm for publication via static site.

Model-specific changes:

## Sim 1. Multiple Risk-Attiudes (no adjustment)

- Significance testing for payoff results from previous batch run data
- Set minimum number of rounds to 50 before checking for convergence

## Sim 2. Evolving Risk-Attiudes (with adjustment)

- Tie-breaker: chose randomly when there is a tie for best payoff when selecting neighbor to emulate
- Set minimum number of rounds to 300 before checking for convergence
- Improved logic for sum of agents with changed risk attitudes in the last adjustment round (part of convergence check)

## Improvements to custom batch run script

- Improve multiprocessing logic
  - Add a timeout on the wait so main loop doesn't wait forever
  - Cycle workers to avoid memory leaks on long runs
- Shift data collection schedule logic to the model: only collect data needed for convergence checks and requested reporting (agent data optional; end of round or adjustment rounds only)

## Miscellaneous

- Jupyter notebooks from prior analysis have been moved to `notebooks/archive/`
- Static html exports from jupyter notebooks have to `docs/analysis/prev/`
