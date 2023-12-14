import statistics
from unittest.mock import patch, Mock

import pytest

from simulatingrisk.hawkdovemulti.model import (
    HawkDoveMultipleRiskModel,
    HawkDoveMultipleRiskAgent,
    RiskState,
)


def test_init():
    model = HawkDoveMultipleRiskModel(5)
    # defaults
    assert model.risk_adjustment is None
    assert model.hawk_odds == 0.5
    assert model.play_neighborhood == 8
    assert model.adjust_neighborhood == 8
    # unused but should be set to default
    assert model.adjust_round_n == 10

    # init with risk adjustment
    model = HawkDoveMultipleRiskModel(
        5,
        play_neighborhood=4,
        hawk_odds=0.2,
        risk_adjustment="adopt",
        adjust_every=5,
        adjust_neighborhood=24,
    )

    assert model.risk_adjustment == "adopt"
    assert model.adjust_round_n == 5
    assert model.hawk_odds == 0.2
    assert model.play_neighborhood == 4
    assert model.adjust_neighborhood == 24

    # handle string none for solara app parameters
    model = HawkDoveMultipleRiskModel(5, risk_adjustment="none")
    assert model.risk_adjustment is None

    # complain about invalid adjustment type
    with pytest.raises(ValueError, match="Unsupported risk adjustment 'bogus'"):
        HawkDoveMultipleRiskModel(3, risk_adjustment="bogus")

    # complain about invalid adjust payoff
    with pytest.raises(ValueError, match="Unsupported adjust payoff option 'bogus'"):
        HawkDoveMultipleRiskModel(3, adjust_payoff="bogus")


def test_init_variable_risk_level():
    model = HawkDoveMultipleRiskModel(5)
    # when risk level is variable/random, agents should have different risk levels
    risk_levels = set([agent.risk_level for agent in model.schedule.agents])
    assert len(risk_levels) > 1


adjustment_testdata = [
    # init parameters, expected adjustment round
    ({"risk_adjustment": None}, None),
    ({"risk_adjustment": "adopt"}, 10),
    ({"risk_adjustment": "average"}, 10),
    ({"risk_adjustment": "average", "adjust_every": 3}, 3),
]


@pytest.mark.parametrize("params,expect_adjust_step", adjustment_testdata)
def test_adjustment_round(params, expect_adjust_step):
    model = HawkDoveMultipleRiskModel(3, **params)

    run_for = (expect_adjust_step or 10) + 1

    # step through the model enough rounds to encounter one adjustment rounds
    # if adjustment is enabled; start at 1 (step count starts at 1)
    for i in range(1, run_for):
        model.step()
        if i == expect_adjust_step:
            assert model.adjustment_round
        else:
            assert not model.adjustment_round


def test_population_risk_category():
    model = HawkDoveMultipleRiskModel(3)
    model.schedule = Mock()

    # majority risk inclined
    model.schedule.agents = [Mock(risk_level=0), Mock(risk_level=1), Mock(risk_level=2)]
    assert model.population_risk_category == RiskState.c1
    # three risk-inclined agents and one risk moderate
    model.schedule.agents.append(Mock(risk_level=4))
    assert model.population_risk_category == RiskState.c2

    # majority risk moderate
    model.schedule.agents = [Mock(risk_level=4), Mock(risk_level=3), Mock(risk_level=5)]
    assert model.population_risk_category == RiskState.c7

    # majority risk avoidant
    model.schedule.agents = [Mock(risk_level=6), Mock(risk_level=7), Mock(risk_level=8)]
    assert model.population_risk_category == RiskState.c12


def test_riskstate_label():
    # enum value or integer value
    assert RiskState.category(RiskState.c1) == "majority risk inclined"
    assert RiskState.category(2) == "majority risk inclined"
    assert RiskState.category(RiskState.c5) == "majority risk moderate"
    assert RiskState.category(6) == "majority risk moderate"
    assert RiskState.category(RiskState.c11) == "majority risk avoidant"
    assert RiskState.category(RiskState.c13) == "no majority"
    assert RiskState.category(13) == "no majority"


def test_most_successful_neighbor():
    # initialize two agents with a mock model
    # first, measure success based on total/cumulative payoff
    agent_total = HawkDoveMultipleRiskAgent(
        1,
        HawkDoveMultipleRiskModel(1, observed_neighborhood=8, adjust_payoff="total"),
        1000,
    )
    agent_recent = HawkDoveMultipleRiskAgent(
        2,
        HawkDoveMultipleRiskModel(1, observed_neighborhood=8, adjust_payoff="recent"),
        1000,
    )

    mock_neighbors = [
        Mock(points=12, recent_points=2),
        Mock(points=14, recent_points=13),
        Mock(points=23, recent_points=5),
        Mock(points=31, recent_points=8),
    ]

    with patch.object(HawkDoveMultipleRiskAgent, "adjust_neighbors", mock_neighbors):
        # comparing by total points
        assert agent_total.most_successful_neighbor.points == 31
        # comparing by recent points
        assert agent_recent.most_successful_neighbor.recent_points == 13


def test_agent_play_adjust():
    mock_model = Mock(
        risk_adjustment="adopt", observed_neighborhood=4, max_risk_level=8
    )
    agent = HawkDoveMultipleRiskAgent(1, mock_model)
    # simulate no neighbors to skip payoff calculation
    with patch.object(
        HawkDoveMultipleRiskAgent, "play_neighbors", new=[]
    ) as mock_adjust_risk:
        with patch.object(HawkDoveMultipleRiskAgent, "adjust_risk") as mock_adjust_risk:
            # when it is not an adjustment round, should not call adjust risk
            mock_model.adjustment_round = False
            agent.play()
            assert mock_adjust_risk.call_count == 0

            # should call adjust risk when the model indicates
            mock_model.adjustment_round = True
            agent.play()
            assert mock_adjust_risk.call_count == 1


def test_adjust_risk_adopt():
    # initialize an agent with a mock model
    agent = HawkDoveMultipleRiskAgent(
        1, Mock(risk_adjustment="adopt", observed_neighborhood=4, max_risk_level=8)
    )
    # set a known risk level
    agent.risk_level = 2
    # adjust wealth as if the model had run
    agent.points = 20
    agent.recent_points = 12
    # set a mock neighbor with more points than current agent
    neighbor = Mock(points=1500, risk_level=3)
    with patch.object(HawkDoveMultipleRiskAgent, "most_successful_neighbor", neighbor):
        agent.adjust_risk()
        # default behavior is to adopt successful risk level
        assert agent.risk_level == neighbor.risk_level
        # recent points should reset
        agent.recent_points = 0

        # now simulate a wealthiest neighbor with fewer points than current agent
        neighbor.points = 12
        agent.recent_points = 5
        neighbor.risk_level = 3
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # risk level should not be changed
        assert agent.risk_level == prev_risk_level
        agent.recent_points = 0


def test_adjust_risk_average():
    # same as previous test, but with average risk adjustment strategy
    agent = HawkDoveMultipleRiskAgent(
        1, Mock(risk_adjustment="average", observed_neighborhood=4, max_risk_level=8)
    )
    # set a known risk level
    agent.risk_level = 2
    # adjust points  as if the model had run
    agent.points = 300
    # set a neighbor with more points than current agent
    neighbor = Mock(points=350, risk_level=3)
    with patch.object(HawkDoveMultipleRiskAgent, "most_successful_neighbor", neighbor):
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # new risk level should be average of previous and most successful
        assert agent.risk_level == round(
            statistics.mean([neighbor.risk_level, prev_risk_level])
        )
