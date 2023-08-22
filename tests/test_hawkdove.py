import math
from unittest.mock import Mock, patch
from collections import Counter

from simulatingrisk.hawkdove.model import HawkDoveModel, HawkDoveAgent, Play


def test_agent_neighbors():
    # initialize model with a small grid, include diagonals
    model = HawkDoveModel(3, include_diagonals=True)
    # every agent should have 8 neighbors when diagonals are included
    assert all([len(agent.neighbors) == 8 for agent in model.schedule.agents])

    # every agent should have 4 neighbors when diagonals are not included
    model = HawkDoveModel(3, include_diagonals=False)
    assert all([len(agent.neighbors) == 4 for agent in model.schedule.agents])


def test_agent_initial_choice():
    grid_size = 100
    model = HawkDoveModel(grid_size, include_diagonals=False)
    # for now, initial choice is random (hawk-odds param still todo)
    initial_choices = [a.choice for a in model.schedule.agents]
    choice_count = Counter(initial_choices)
    # default should be around a 50/50 split
    half_agents = model.num_agents / 2.0
    for choice, total in choice_count.items():
        assert math.isclose(total, half_agents, rel_tol=0.05)


def test_num_hawk_neighbors():
    # initialize an agent with a mock model
    agent = HawkDoveAgent(1, Mock())
    mock_neighbors = [
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.DOVE),
    ]

    with patch.object(HawkDoveAgent, "neighbors", mock_neighbors):
        assert agent.num_hawk_neighbors == 3


def test_agent_choose():
    agent = HawkDoveAgent(1, Mock())
    # on the first round, nothing should happen (uses initial choice)
    agent.model.schedule.steps = 0
    agent.choose()
    assert agent.last_choice is None

    # on subsequent rounds, choose based on neighbors and risk level
    agent.model.schedule.steps = 1

    # given a specified number of hawk neighbors and risk level
    with patch.object(HawkDoveAgent, "num_hawk_neighbors", 3):
        # an agent with `r=0` will always take the risky choice
        # (any risk is acceptable).
        agent.risk_level = 0
        agent.choose()
        assert agent.choice == Play.HAWK

        # risk level 2 with 3 hawks will play hawk
        # (but this doesn't really make sense...)
        agent.risk_level = 2
        agent.choose()
        assert agent.choice == Play.HAWK

        # risk level three will not
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
    # If I play DOVE and neighbor plays DOVE: 2
    # If I play DOVE and neighbor plays HAWK: 1
    # If I play HAWK and neighbor plays HAWK: 0

    agent = HawkDoveAgent(1, Mock())
    other_agent = HawkDoveAgent(2, Mock())
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
    assert agent.payoff(other_agent) == 2
    assert other_agent.payoff(agent) == 2
