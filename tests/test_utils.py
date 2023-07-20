from collections import Counter
import math
import pytest

from simulatingrisk.utils import coinflip


test_probabilities = [
    (None),
    (0.5),
    (0.2),
    (0.8),
]


@pytest.mark.parametrize("weight", test_probabilities)
def test_coinflip_weights(weight):
    # test that coin flip method weight logic is working properly

    # run 100 times so we can check the percentage of
    # choices made is close to expected weight
    results = []
    total_runs = 100
    for i in range(total_runs):
        if weight:
            results.append(coinflip(weight=weight))
        else:
            # for None, don't specify the weight
            results.append(coinflip())

    # use counter to tally the results
    result_count = Counter(results)

    # the expected value is the probability times number of times we ran it
    # - unspecified weight should be equivalent to 0.5
    if weight is None:
        weight = 0.5
    expected = total_runs * weight
    assert math.isclose(result_count[0], expected, abs_tol=total_runs * 0.2)


def test_coinflip_choices():
    # test using non-default choices
    choices = ["a", "b"]
    results = []
    total_runs = 10
    for i in range(total_runs):
        results.append(coinflip(choices=choices))

    # use counter to tally the results
    result_count = Counter(results)
    # we should only have choices within our specified set
    assert set(result_count.keys()) == set(choices)
    # we expect an equal distribution of those choices
    for choice in choices:
        assert math.isclose(result_count[choice], 5, abs_tol=total_runs * 0.5)
