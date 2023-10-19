import math
from unittest.mock import Mock, patch
from collections import Counter

import pytest

from simulatingrisk.hawkdove.model import (
    HawkDoveAgent,
    Play,
    HawkDoveSingleRiskModel,
    HawkDoveSingleRiskAgent,
)
from simulatingrisk.hawkdovevar.model import HawkDoveVariableRiskModel


def test_agent_neighbors():
    # initialize model with a small grid, include diagonals
    model = HawkDoveSingleRiskModel(3, include_diagonals=True, agent_risk_level=4)
    # every agent should have 8 neighbors when diagonals are included
    assert all([len(agent.neighbors) == 8 for agent in model.schedule.agents])

    # every agent should have 4 neighbors when diagonals are not included
    model = HawkDoveSingleRiskModel(3, include_diagonals=False, agent_risk_level=2)
    assert all([len(agent.neighbors) == 4 for agent in model.schedule.agents])


def test_agent_initial_choice():
    grid_size = 100
    model = HawkDoveSingleRiskModel(
        grid_size, include_diagonals=False, agent_risk_level=5
    )
    # for now, initial choice is random (hawk-odds param still todo)
    initial_choices = [a.choice for a in model.schedule.agents]
    choice_count = Counter(initial_choices)
    # default should be around a 50/50 split
    half_agents = model.num_agents / 2.0
    for choice, total in choice_count.items():
        assert math.isclose(total, half_agents, rel_tol=0.05)


def test_agent_initial_choice_hawkodds():
    grid_size = 100
    # specify hawk-odds other than 05
    model = HawkDoveSingleRiskModel(
        grid_size, include_diagonals=False, hawk_odds=0.3, agent_risk_level=2
    )
    initial_choices = [a.choice for a in model.schedule.agents]
    choice_count = Counter(initial_choices)
    # expect about 30% hawks
    expected_hawks = model.num_agents * 0.3
    assert math.isclose(choice_count[Play.HAWK], expected_hawks, rel_tol=0.05)


def test_base_agent_risk_level():
    # base class should raise error because method to set risk level is not defined
    with pytest.raises(NotImplementedError):
        HawkDoveAgent(1, Mock())


def test_agent_initial_risk_level():
    # single risk agent sets risk level based on model
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=2))
    assert agent.risk_level == 2


def test_agent_repr():
    agent_id = 1
    risk_level = 3
    agent = HawkDoveSingleRiskAgent(agent_id, Mock(agent_risk_level=risk_level))
    assert repr(agent) == f"<HawkDoveSingleRiskAgent id={agent_id} r={risk_level}>"


def test_model_single_risk_level():
    risk_level = 3
    model = HawkDoveSingleRiskModel(
        5, include_diagonals=True, agent_risk_level=risk_level
    )
    for agent in model.schedule.agents:
        assert agent.risk_level == risk_level

    # handle zero properly (should not be treated the same as None)
    risk_level = 0
    model = HawkDoveSingleRiskModel(
        5, include_diagonals=True, agent_risk_level=risk_level
    )
    for agent in model.schedule.agents:
        assert agent.risk_level == risk_level


def test_variable_risk_level():
    model = HawkDoveVariableRiskModel(
        5,
        include_diagonals=True,
    )
    # when risk level is variable/random, agents should have different risk levels
    risk_levels = set([agent.risk_level for agent in model.schedule.agents])
    assert len(risk_levels) > 1


def test_num_dove_neighbors():
    # initialize an agent with a mock model
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=2))
    mock_neighbors = [
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.DOVE),
    ]

    with patch.object(HawkDoveSingleRiskAgent, "neighbors", mock_neighbors):
        assert agent.num_dove_neighbors == 1


def test_agent_choose():
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=3))
    # on the first round, nothing should happen (uses initial choice)
    agent.model.schedule.steps = 0
    agent.choose()
    assert agent.last_choice is None

    # on subsequent rounds, choose based on neighbors and risk level
    agent.model.schedule.steps = 1

    # given a specified number of dove neighbors and risk level
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 3):
        # an agent with `r=0` will always take the risky choice
        # (any risk is acceptable).
        agent.risk_level = 0
        agent.choose()
        assert agent.choice == Play.HAWK

        # risk level 2 with 3 doves will play dove
        agent.risk_level = 2
        agent.choose()
        assert agent.choice == Play.HAWK

        # risk level three with 3 doves will play dove
        # (strictly greater comparison)
        agent.risk_level = 3
        agent.choose()
        assert agent.choice == Play.DOVE

        # agent with risk level 8 will always play dove
        agent.risk_level = 8
        agent.choose()
        assert agent.choice == Play.DOVE

        # test last choice is updated when choose runs
        agent.choice = "foo"  # set to confirm stored
        agent.choose()
        assert agent.last_choice == "foo"


def test_agent_payoff():
    # If I play HAWK and neighbor plays DOVE: 3
    # If I play DOVE and neighbor plays DOVE: 2.1
    # If I play DOVE and neighbor plays HAWK: 1
    # If I play HAWK and neighbor plays HAWK: 0

    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=2))
    other_agent = HawkDoveSingleRiskAgent(2, Mock(agent_risk_level=3))
    # If I play HAWK and neighbor plays DOVE: 3
    agent.choice = Play.HAWK
    other_agent.choice = Play.DOVE
    assert agent.payoff(other_agent) == 3
    # inverse: play DOVE and neighbor plays HAWK: 1
    assert other_agent.payoff(agent) == 1

    # if both play hawk, payoff is zero for both
    other_agent.choice = Play.HAWK
    assert agent.payoff(other_agent) == 0
    assert other_agent.payoff(agent) == 0

    # if both play dove, payoff is two for both
    agent.choice = Play.DOVE
    other_agent.choice = Play.DOVE
    assert agent.payoff(other_agent) == 2.1
    assert other_agent.payoff(agent) == 2.1
