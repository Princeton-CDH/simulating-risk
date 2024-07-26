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


def test_agent_neighbors():
    # initialize model with a small grid, neighborhood of 8
    model = HawkDoveSingleRiskModel(3, play_neighborhood=8, agent_risk_level=4)
    # every agent should have 8 neighbors when diagonals are included
    assert all([len(agent.play_neighbors) == 8 for agent in model.schedule.agents])

    # neighborhood of 4
    model = HawkDoveSingleRiskModel(3, play_neighborhood=4, agent_risk_level=2)
    assert all([len(agent.play_neighbors) == 4 for agent in model.schedule.agents])

    # neighborhood of 24 (grid needs to be at least 5x5)
    model = HawkDoveSingleRiskModel(5, play_neighborhood=24, agent_risk_level=5)
    assert all([len(agent.play_neighbors) == 24 for agent in model.schedule.agents])


def test_bad_gridsize():
    # anything less than 5 should not allow play neighborhood of 24
    for grid_size in [3, 4]:
        with pytest.raises(ValueError):
            HawkDoveSingleRiskModel(3, play_neighborhood=24, agent_risk_level=5)
        with pytest.raises(ValueError):
            HawkDoveSingleRiskModel(3, observed_neighborhood=24, agent_risk_level=5)


def test_agent_initial_choice():
    grid_size = 100
    model = HawkDoveSingleRiskModel(grid_size, agent_risk_level=5)
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
    model = HawkDoveSingleRiskModel(grid_size, hawk_odds=0.3, agent_risk_level=2)
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
    assert (
        repr(agent)
        == f"<HawkDoveSingleRiskAgent id={agent_id} r={risk_level} points=0>"
    )


def test_model_single_risk_level():
    risk_level = 3
    model = HawkDoveSingleRiskModel(5, agent_risk_level=risk_level)
    for agent in model.schedule.agents:
        assert agent.risk_level == risk_level

    # handle zero properly (should not be treated the same as None)
    risk_level = 0
    model = HawkDoveSingleRiskModel(5, agent_risk_level=risk_level)
    for agent in model.schedule.agents:
        assert agent.risk_level == risk_level


def test_bad_neighborhood_size():
    with pytest.raises(ValueError):
        HawkDoveSingleRiskModel(3, play_neighborhood=3, agent_risk_level=6)
    with pytest.raises(ValueError):
        agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=2))
        agent.get_neighbors(5)


def test_observed_neighborhood_size():
    # observed neighborhood size is also configurable
    # common options, irrelevant for this test
    opts = {"agent_risk_level": 1, "play_neighborhood": 4}
    model = HawkDoveSingleRiskModel(3, observed_neighborhood=4, **opts)
    assert model.observed_neighborhood == 4
    model = HawkDoveSingleRiskModel(3, observed_neighborhood=8, **opts)
    assert model.observed_neighborhood == 8
    model = HawkDoveSingleRiskModel(5, observed_neighborhood=24, **opts)
    assert model.observed_neighborhood == 24
    with pytest.raises(ValueError):
        HawkDoveSingleRiskModel(3, observed_neighborhood=23, **opts)


def test_num_dove_neighbors():
    # initialize an agent with a mock model
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=2))
    mock_neighbors = [
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.HAWK),
        Mock(last_choice=Play.DOVE),
    ]

    with patch.object(HawkDoveSingleRiskAgent, "observed_neighbors", mock_neighbors):
        assert agent.num_dove_neighbors == 1


def test_agent_choose():
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=3))
    # on the first round, nothing should happen (uses initial choice)
    agent.model.schedule.steps = 0
    # disable random play for now
    agent.model.random_play_odds = 0
    agent.choose()

    # on subsequent rounds, choose based on neighbors and risk level
    agent.model.schedule.steps = 1

    # given a specified number of dove neighbors and risk level
    with patch.object(HawkDoveAgent, "proportional_num_dove_neighbors", 3):
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
        # (greater than or equal)
        agent.risk_level = 3
        agent.choose()
        assert agent.choice == Play.HAWK

        # agent with risk level 8 will always play dove
        agent.risk_level = 8
        agent.choose()
        assert agent.choice == Play.DOVE


@patch("simulatingrisk.hawkdove.model.coinflip")
def test_agent_choose_random(mock_coinflip):
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=3))
    agent.model.schedule.steps = 1
    # reset after init, which calls coinflip for initial play
    mock_coinflip.reset_mock()
    with patch.object(HawkDoveAgent, "proportional_num_dove_neighbors", 2):
        # if random play is disabled, should not flip a coin
        agent.model.random_play_odds = 0
        agent.choose()
        assert mock_coinflip.call_count == 0

        # some chance of random play
        agent.model.random_play_odds = 0.5
        mock_coinflip.side_effect = [True, Play.DOVE]
        agent.choose()
        # should call twice: once for random play, once for choice
        assert mock_coinflip.call_count == 2
        # called for random play with model odds
        mock_coinflip.assert_any_call(
            [True, False], weight=agent.model.random_play_odds
        )
        # called a second time to determine which play to make
        mock_coinflip.assert_any_call([Play.HAWK, Play.DOVE])
        assert agent.choice == Play.DOVE


def test_proportional_num_dove_neighbors():
    model = HawkDoveSingleRiskModel(4, agent_risk_level=3)
    agent = HawkDoveSingleRiskAgent(1, model)

    ## equal play/observed; scales to 8 (risk level range)
    model.observed_neighborhood = 4
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 4):
        assert agent.proportional_num_dove_neighbors == 8
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 3):
        assert agent.proportional_num_dove_neighbors == 6
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 2):
        assert agent.proportional_num_dove_neighbors == 4

    model.observed_neighborhood = 8
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 5):
        assert agent.proportional_num_dove_neighbors == 5
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 6):
        assert agent.proportional_num_dove_neighbors == 6
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 7):
        assert agent.proportional_num_dove_neighbors == 7

    # observe more than 8
    model.observed_neighborhood = 24
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 20):
        assert agent.proportional_num_dove_neighbors == 7
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 23):
        assert agent.proportional_num_dove_neighbors == 8
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 6):
        assert agent.proportional_num_dove_neighbors == 2


def test_agent_choose_when_observe_play_differ():
    # confirm that adjusted value is used to determine play

    model = HawkDoveSingleRiskModel(
        5, agent_risk_level=3, observed_neighborhood=24, play_neighborhood=8
    )
    agent = HawkDoveSingleRiskAgent(3, model)
    with patch.object(HawkDoveAgent, "num_dove_neighbors", 5):
        agent.choose() == Play.DOVE

    with patch.object(HawkDoveAgent, "num_dove_neighbors", 6):
        agent.choose() == Play.HAWK


def test_agent_play():
    agent = HawkDoveSingleRiskAgent(1, Mock(agent_risk_level=3))
    # on the first round, last choice should be unset
    assert agent.last_choice is None
    assert agent.points == 0

    # set initial choice and supply mock neighbors
    # so we can test expected results
    agent.choice = Play.HAWK
    neighbor_hawk = Mock(choice=Play.HAWK)
    neighbor_dove = Mock(choice=Play.DOVE)
    with patch.object(HawkDoveAgent, "play_neighbors", [neighbor_hawk, neighbor_dove]):
        agent.play()
        # should get 3 points against dove and 0 against the hawk
        assert agent.points == 3 + 0
        # should store current choice for next round
        assert agent.last_choice == Play.HAWK


def test_agent_payoff():
    # If I play HAWK and neighbor plays DOVE: 3
    # If I play DOVE and neighbor plays DOVE: 2
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
    assert agent.payoff(other_agent) == 2
    assert other_agent.payoff(agent) == 2
