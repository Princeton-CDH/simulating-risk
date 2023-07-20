from collections import Counter
import math
import pytest

from simulatingrisk.risky_food.model import RiskyFoodModel, FoodStatus


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
