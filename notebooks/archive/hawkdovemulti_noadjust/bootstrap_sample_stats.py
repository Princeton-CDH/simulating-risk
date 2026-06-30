#!/usr/bin/env python
#
# adapted from notebok code to run boostrap sampling outside of a notebook
#
import csv
from pathlib import Path

import polars as pl
from tqdm import tqdm

notebook_dir = Path(__file__).parent
# path relative to notebook dir is  "../../data/hawkdovemulti/
data_dir = notebook_dir.parent.parent / "data" / "hawkdovemulti"

# which batch run data to use;
# use variable to ensure we use matching agent and model data
batch_run_date = "2025-07-24T120337_924060"

# load agent data, drop unneeded columns,
# add numeric value 1 for played hawk, 0 for played dove
df = (
    pl.read_csv(data_dir / f"{batch_run_date}_agent.csv")
    .drop(
        "risk_level_changed"
    )  # drop risk_level_changed; not relevant here (no adjustment = no changes)
    .rename(
        {"risk_level": "risk_attitude"}
    )  # code still uses risk_level internally; relabel as risk attitude
    .with_columns(
        # add a numeric field to turn choice of play to 1/0 hawk, for aggregation
        played_hawk=pl.when(pl.col("choice").eq("hawk"))
        .then(1)
        .otherwise(0)
    )
)
print(f"Loaded batch run data ({df.height:,} rows)")

# identify the last round of each run
# for both wealth analysis and model parameters,
# we want to look at the last round (Step) of each run
last_round_df = df.group_by("RunId").agg(pl.col("Step").max())

# load model data and filter to last round for each run
full_model_df = pl.read_csv(data_dir / f"{batch_run_date}_model.csv")
model_df = last_round_df.join(full_model_df, on=["RunId", "Step"], how="left")
# limit to only those fields that are needed for our analysis
model_df = model_df.select(
    "RunId",
    "iteration",
    "risk_distribution",
    "play_neighborhood",
    "observed_neighborhood",
    "grid_size",
    "Step",
)
model_df = model_df.filter(pl.col.grid_size.is_not_null())
print(f"Loaded model data {model_df.height:,} rows")

# combine the last round dataframe and full agent dataframe
# to get just the last round of each run
agents_last_round_df = (
    last_round_df.join(df, on=["RunId", "Step"], how="left")
    # join on model parameters, for filtering and scaling by play neighborhood
    .join(model_df, on=["RunId", "iteration"]).with_columns(
        # calculate a scaled points value so we can compare
        # across runs with different length and play neighborhood
        scaled_points=pl.col("points")
        .truediv(pl.col("play_neighborhood"))
        .truediv(pl.col("Step"))
        .mul(100)
    )
)

print(f"Identified agent last round data {agents_last_round_df.height:,} rows")

# delete things that are no longer needed to save memory
del model_df
del df
del full_model_df

print("Beginning bootstrap sampling ...")
sample_fraction = 0.5  # 0.5 is crashing in memory, still over 1mil per sample
iterations = 10_000  # 5_000

stats_file = data_dir / "payoff_bootstrap_stats_2pct_10k.csv"

with stats_file.open("w") as outfile:
    csvwriter = csv.DictWriter(
        outfile, fieldnames=["risk_attitude", "mean", "median", "q1", "q3"]
    )
    csvwriter.writeheader()
    for _ in tqdm(range(iterations), total=iterations):
        resample_stats_df = (
            agents_last_round_df.select("risk_attitude", "scaled_points")
            .sample(fraction=sample_fraction, with_replacement=True)
            .lazy()
            .group_by("risk_attitude")
            .agg(
                mean=pl.col.scaled_points.mean(),
                median=pl.col.scaled_points.median(),
                q1=pl.col.scaled_points.quantile(0.25),
                # q2=pl.col.scaled_points.quantile(0.5),
                q3=pl.col.scaled_points.quantile(0.75),
            )
        )
        csvwriter.writerows(resample_stats_df.collect().to_dicts())


# collected_stats = pl.collect_all(
#     [
#         agents_last_round_df.select("risk_attitude", "scaled_points")
#         .sample(fraction=sample_fraction, with_replacement=True)
#         .lazy()
#         .group_by("risk_attitude")
#         .agg(
#             mean=pl.col.scaled_points.mean(),
#             median=pl.col.scaled_points.median(),
#             q1=pl.col.scaled_points.quantile(0.25),
#             # q2=pl.col.scaled_points.quantile(0.5),
#             q3=pl.col.scaled_points.quantile(0.75),
#         )
#         for _ in range(iterations)
#     ]
# )

# lazy_stats_df = pl.concat(collected_stats)
# lazy_stats_df.write_csv(data_dir / "payoff_bootstrap_stats.csv")
