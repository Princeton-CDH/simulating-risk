from collections import Counter
import math
from unittest.mock import Mock, patch
import statistics

import pytest

from simulatingrisk.risky_bet.model import RiskyBetModel, Gambler
from simulatingrisk.risky_bet.server import risk_index


def test_call_risky_bet():
    # test risk bet generating payoff probability and calling the bet

    # initialize model with a few agents (3x3 grid)
    model = RiskyBetModel(3)

    probabilities = []
    results = []
    total_runs = 10
    for i in range(total_runs):
        model.step()
        probabilities.append(model.prob_risky_payoff)
        results.append(model.risky_payoff)

    # use counter to tally the results
    result_count = Counter(results)

    # confirm probabilities are in expected range
    assert all([(p > 0.0 and p < 1.0) for p in probabilities])
    # not sure how to reliably test the payoff...
    # payoff results depend on the probabilities,
    # but should be some even-ish split
    assert math.isclose(result_count[True], total_runs / 2, abs_tol=3)


def test_adjustment_round():
    model = RiskyBetModel(3)

    # run for nine rounds, none of them should be adjustment rounds
    for i in range(9):
        model.step()
        assert not model.adjustment_round
    # tenth round is an adjustment round
    model.step()
    assert model.adjustment_round
    # next round is not
    model.step()
    assert not model.adjustment_round


def test_gambler_neighbors():
    # initialize model with a few agents (3x3 grid)
    model = RiskyBetModel(4)
    model.step()

    # every agent should have 4 neighbors,
    # even if they are on the edge of the grid
    for agent in model.schedule.agents:
        assert len(agent.neighbors) == 4


def test_gambler_wealthiestneighbor():
    # initialize an agent with a mock model
    agent = Gambler(1, Mock(), 1000)
    mock_neighbors = [
        Mock(wealth=1),
        Mock(wealth=45),
        Mock(wealth=232),
        Mock(wealth=32),
    ]

    with patch.object(Gambler, "neighbors", mock_neighbors):
        assert agent.wealthiest_neighbor.wealth == 232


def test_gambler_adjust_risk_adopt():
    # initialize an agent with a mock model
    agent = Gambler(1, Mock(risk_adjustment="adopt"), 1000)
    # set a known risk level
    agent.risk_level = 0.3
    # adjust wealth as if the model had run
    agent.wealth = 300
    # set a mock wealthiest neighbor with more wealth than current agent
    neighbor = Mock(wealth=1500, risk_level=0.2)
    with patch.object(Gambler, "wealthiest_neighbor", neighbor):
        agent.adjust_risk()
        # default behavior is to adopt successful risk level
        assert agent.risk_level == neighbor.risk_level
        # wealth should reset to initial value
        assert agent.wealth == agent.initial_wealth

        # now simulate a wealthiest neighbor with less wealth than current agent
        neighbor.wealth = 240
        neighbor.risk_level = 0.4
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # risk level should not be changed
        assert agent.risk_level == prev_risk_level


def test_gambler_adjust_risk_average():
    # same as previous test, but with average risk adjustment strategy
    agent = Gambler(1, Mock(risk_adjustment="average"), 1000)
    # set a known risk level
    agent.risk_level = 0.7
    # adjust wealth as if the model had run
    agent.wealth = 300
    # set a mock wealthiest neighbor with more wealth than current agent
    neighbor = Mock(wealth=1500, risk_level=0.2)
    with patch.object(Gambler, "wealthiest_neighbor", neighbor):
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # new risk level should be average of previous and most successful
        assert agent.risk_level == statistics.mean(
            [neighbor.risk_level, prev_risk_level]
        )


test_risk_index_bins = [
    (0.04, 0),  # first bin is 0 - 0.05
    (0.09, 1),  # 2nd : 0.05 - 0.15
    (0.18, 2),  # 3nd : 0.15 - 0.25
    (0.32, 3),  # 3nd : 0.25 - 0.35
    (0.98, 10),  # last bin is 0.95 - 1
]


@pytest.mark.parametrize("risk_level,expected_bin", test_risk_index_bins)
def test_risk_index(risk_level, expected_bin):
    assert risk_index(risk_level) == expected_bin
