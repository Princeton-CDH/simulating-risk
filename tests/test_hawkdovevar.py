import statistics
from unittest.mock import patch, Mock

import pytest

from simulatingrisk.hawkdovevar.model import (
    HawkDoveVariableRiskModel,
    HawkDoveVariableRiskAgent,
)


def test_init():
    model = HawkDoveVariableRiskModel(5)
    # defaults
    assert model.risk_adjustment is None
    assert model.hawk_odds == 0.5
    assert model.include_diagonals is True
    # unused but should be set to default
    assert model.adjust_round_n == 10

    # init with risk adjustment
    model = HawkDoveVariableRiskModel(
        5,
        include_diagonals=False,
        hawk_odds=0.2,
        risk_adjustment="adopt",
        adjust_every=5,
    )

    assert model.risk_adjustment == "adopt"
    assert model.adjust_round_n == 5
    assert model.hawk_odds == 0.2
    assert model.include_diagonals is False

    # handle string none for solara app parameters
    model = HawkDoveVariableRiskModel(5, risk_adjustment="none")
    assert model.risk_adjustment is None

    # complain about invalid adjustment type
    with pytest.raises(ValueError, match="Unsupported risk adjustment 'bogus'"):
        HawkDoveVariableRiskModel(3, risk_adjustment="bogus")


def test_init_variable_risk_level():
    model = HawkDoveVariableRiskModel(
        5,
        include_diagonals=True,
    )
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
    model = HawkDoveVariableRiskModel(3, **params)

    run_for = (expect_adjust_step or 10) + 1

    # step through the model enough rounds to encounter one adjustment rounds
    # if adjustment is enabled; start at 1 (step count starts at 1)
    for i in range(1, run_for):
        model.step()
        if i == expect_adjust_step:
            assert model.adjustment_round
        else:
            assert not model.adjustment_round


def test_most_successful_neighbor():
    # initialize an agent with a mock model
    agent = HawkDoveVariableRiskAgent(1, Mock(), 1000)
    mock_neighbors = [
        Mock(points=2),
        Mock(points=4),
        Mock(points=23),
        Mock(points=31),
    ]

    with patch.object(HawkDoveVariableRiskAgent, "neighbors", mock_neighbors):
        assert agent.most_successful_neighbor.points == 31


def test_agent_play_adjust():
    mock_model = Mock(risk_adjustment="adopt")
    agent = HawkDoveVariableRiskAgent(1, mock_model)
    # simulate no neighbors to skip payoff calculation
    with patch.object(
        HawkDoveVariableRiskAgent, "neighbors", new=[]
    ) as mock_adjust_risk:
        with patch.object(HawkDoveVariableRiskAgent, "adjust_risk") as mock_adjust_risk:
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
    agent = HawkDoveVariableRiskAgent(1, Mock(risk_adjustment="adopt"))
    # set a known risk level
    agent.risk_level = 2
    # adjust wealth as if the model had run
    agent.points = 20
    # set a mock neighbor with more points than current agent
    neighbor = Mock(points=1500, risk_level=3)
    with patch.object(HawkDoveVariableRiskAgent, "most_successful_neighbor", neighbor):
        agent.adjust_risk()
        # default behavior is to adopt successful risk level
        assert agent.risk_level == neighbor.risk_level

        # now simulate a wealthiest neighbor with fewer points than current agent
        neighbor.points = 12
        neighbor.risk_level = 3
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # risk level should not be changed
        assert agent.risk_level == prev_risk_level


def test_adjust_risk_average():
    # same as previous test, but with average risk adjustment strategy
    agent = HawkDoveVariableRiskAgent(1, Mock(risk_adjustment="average"))
    # set a known risk level
    agent.risk_level = 2
    # adjust points  as if the model had run
    agent.points = 300
    # set a neighbor with more points than current agent
    neighbor = Mock(points=350, risk_level=3)
    with patch.object(HawkDoveVariableRiskAgent, "most_successful_neighbor", neighbor):
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # new risk level should be average of previous and most successful
        assert agent.risk_level == round(
            statistics.mean([neighbor.risk_level, prev_risk_level])
        )
