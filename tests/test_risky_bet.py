from collections import Counter
import math

from simulatingrisk.risky_bet.model import RiskyBetModel


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

    for metaround in range(3):
        # run for nine rounds, none of them should be adjustment rounds
        for i in range(9):
            model.step()
            assert model.adjustment_round is False
        # tenth round is an adjustment round
        model.step()
        assert model.adjustment_round


def test_riskygambler_neighbors():
    # initialize model with a few agents (3x3 grid)
    model = RiskyBetModel(4)
    model.step()

    # every agent should have 4 neighbors,
    # even if they are on the edge of the grid
    for agent in model.schedule.agent_buffer():
        assert len(agent.neighbors) == 4
