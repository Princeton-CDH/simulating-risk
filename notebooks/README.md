# Simulating Risk notebooks

This folder includes Jupyter/Colab notebooks associated with the 
Simulating Risk project.  Some notebooks allow running the simulations 
directly within a notebook; others are for analysis of simulation results.

Batch analysis references data files that are too large to include on GitHub;
download from [Google Drive](https://drive.google.com/drive/folders/1ASQ9_IqeBHhyyFzuqcrWtdebdLiwqQp2)
and put in the top-level `data/` folder.

## Hawk/Dove - multiple risk attitudes

Refer to [game description](../simulatingrisk/hawkdovemulti) for details.

### Without adjustment

* [preliminary analysis](hawkdovemulti_noadjust/hawkdove_variable_r_analysis.ipynb) - simulation length, % hawk by risk level, points by risk level

### With adjustment

* [population risk category analysis](hawkdovemulti_adjust/hawkdovevar_population_risk_category.ipynb) - analysis based on data from 2023-10
* [analysis of parameter correlation with population risk attitudes](hawkdovemulti_adjust/hawkdovemulti_agentrisktotals.ipynb) - analysis based on data from 2024-02
* [run-length analysis, with parameter correlation](notebooks/hawkdovemulti_adjust/hawkdovemulti_runlength.ipynb) - data from 2024-02
* [parameter analysis](hawkdovemulti_adjust/hawkdovemulti_polars.ipynb) - data from 2024-02; using Polars to analyze larger scale of data; similar to earlier parameter correlation analysis
* [adjustment strategy and recent/total payoff](hawkdovemulti_adjust/hdm_analysis.ipynb) - risk attitudes across runs, population category, and paired statistical parameter testing 
* [convergence & population distribution](hawkdovemulti_adjust/hdm_c7_riskdistribution.ipynb) - data from 2024-02; includes population category analysis based on initial risk distribution
* [risk adjustment & run length](hawkdovemulti_adjust/hdm_riskadjust_runlength.ipynb) - Convergence and run length based on population measure of change; data from 2024-07
* [convergence and population with initial hawk odds](/hawkdovemulti_adjust/hdm_c7_hawkodds.ipynb) - data from 2024-03

## Hawk/Dove - single risk attitude 

Refer to [game description](../simulatingrisk/hawkdove) for details.

* [batch analysis](hakwdove_single_r/hawkdove_single_r_analysis.ipynb)


## Risky Bet

Refer to [game description](../simulatingrisk/risky_bet) for details.

* [simulation](riskybet/riskybet_simulation.ipynb)
* [batch analysis](riskybet/riskybet_batch_analysis.ipynb)

## Risky Food

Refer to [game description](../simulatingrisk/risky_food) for details.

* [simulation](riskyfood/riskyfood_simulation.ipynb)
* [batch analysis](riskyfood/riskyfood_batch_analysis.ipynb) 


-----

## Snapshot export

To convert Jupyter notebooks to html snapshot, use nbconvert.

HTML notebooks should be put under top-level `docs/` folder.

```shell
jupyter-nbconvert --to html notebooks/hawkdovemulti_adjust/hawkdovemulti_agentrisktotals.ipynb --output-dir=docs/notebooks/hawkdovemulti-adjust/ --output=parameter_analysis
jupyter-nbconvert --to html notebooks/hawkdovemulti_adjust/hdm_analysis.ipynb --output-dir=docs/notebooks/hawkdovemulti-adjust/
jupyter-nbconvert --to html --output-dir=docs/notebooks/hawkdovemulti-adjust/ notebooks/hawkdovemulti_adjust/hdm_c7_riskdistribution.ipynb
```


