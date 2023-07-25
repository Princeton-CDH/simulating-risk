from collections import Counter
import math

import pytest

from simulatingrisk.risky_food.model import RiskyFoodModel, FoodStatus, Agent


test_probabilities = [
    (0.5),
    (0.2),
    (0.8),
]


@pytest.mark.parametrize("prob_notcontaminated", test_probabilities)
def test_risky_food_status(prob_notcontaminated):
    # test that food status choice is weighted properly
    # by probability of not being contaminated

    # NOTE: this is redundant now that we've refactored the logic
    # into a reusable coin flip method; keeping to confirm refactor works

    # initialize model with one agent
    model = RiskyFoodModel(1)
    model.prob_notcontaminated = prob_notcontaminated

    results = []
    total_runs = 100
    for i in range(total_runs):
        results.append(model.get_risky_food_status())

    # use counter to tally the results
    result_count = Counter(results)

    # the expected value is the probability times number of times we ran it
    expected = total_runs * model.prob_notcontaminated
    assert math.isclose(
        result_count[FoodStatus.NOTCONTAMINATED], expected, abs_tol=total_runs * 0.1
    )


def test_agent_init():
    model = RiskyFoodModel(1)
    agent_id = 123
    agent = Agent(agent_id, model)
    assert agent.model == model
    assert agent.unique_id == agent_id
    # random risk level
    assert agent.risk_level >= 0.0 and agent.risk_level <= 1.0

    # assigned risk level
    risk = 0.4
    agent2 = Agent(1, model, risk_level=risk)
    assert agent2.risk_level == risk

    # allow zero risk (should not get a random value)
    agent0 = Agent(1, model, risk_level=0)
    assert agent0.risk_level == 0
