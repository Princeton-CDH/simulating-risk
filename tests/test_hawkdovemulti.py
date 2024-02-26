import statistics
from unittest.mock import patch, Mock

import pytest

from simulatingrisk.hawkdove.model import Play
from simulatingrisk.hawkdovemulti.model import (
    HawkDoveMultipleRiskModel,
    HawkDoveMultipleRiskAgent,
    RiskState,
)


def test_init():
    model = HawkDoveMultipleRiskModel(5)
    # defaults
    assert model.risk_adjustment == "adopt"
    assert model.hawk_odds == 0.5
    assert model.play_neighborhood == 8
    assert model.adjust_neighborhood == 8
    assert model.adjust_round_n == 10
    assert model.risk_distribution == "uniform"

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


def test_total_per_risk_level():
    model = HawkDoveMultipleRiskModel(3)
    model.schedule = Mock()
    # add a few agents with different risk levels
    mock_agents = [
        Mock(risk_level=0),
        Mock(risk_level=1),
        Mock(risk_level=1),
        Mock(risk_level=2),
        Mock(risk_level=2),
        Mock(risk_level=2),
        Mock(risk_level=5),
    ]
    model.schedule.agents = mock_agents

    totals = model.total_per_risk_level
    assert totals[0] == 1
    assert totals[1] == 2
    assert totals[2] == 3
    assert totals[4] == 0
    assert totals[5] == 1
    assert totals[8] == 0

    # check caching works as desired
    mock_agents.append(Mock(risk_level=8))
    model.schedule.agents = mock_agents
    # cached total should not change even though agents have changed
    assert model.total_per_risk_level[8] == 0
    # step should reset catched property
    with patch("builtins.super"):
        model.step()
    # now the count should be updated
    assert model.total_per_risk_level[8] == 1


def test_total_rN_attr():
    # dynamic attributes to get total per risk level, for data collection
    model = HawkDoveMultipleRiskModel(3)
    model.schedule = Mock()
    # add a few agents with different risk levels
    model.schedule.agents = [
        Mock(risk_level=0),
        Mock(risk_level=1),
        Mock(risk_level=1),
        Mock(risk_level=2),
        Mock(risk_level=2),
        Mock(risk_level=2),
    ]
    assert model.total_r0 == 1
    assert model.total_r1 == 2
    assert model.total_r2 == 3
    assert model.total_r4 == 0

    # error handling
    # - non-numeric
    with pytest.raises(AttributeError):
        model.total_rfour
    # - out of bounds
    with pytest.raises(AttributeError):
        model.total_r23
    # - unsupported attribute
    with pytest.raises(AttributeError):
        model.some_other_total


def test_population_risk_category():
    model = HawkDoveMultipleRiskModel(3)
    model.schedule = Mock()

    # majority risk inclined
    model.schedule.agents = [Mock(risk_level=0), Mock(risk_level=1), Mock(risk_level=2)]
    assert model.population_risk_category == RiskState.c1
    # three risk-inclined agents and one risk moderate
    del model.total_per_risk_level  #  reset cached property
    model.schedule.agents.append(Mock(risk_level=4))
    assert model.population_risk_category == RiskState.c2

    # majority risk moderate
    model.schedule.agents = [Mock(risk_level=4), Mock(risk_level=5), Mock(risk_level=6)]
    del model.total_per_risk_level  #  reset cached property
    assert model.population_risk_category == RiskState.c7

    # majority risk avoidant
    model.schedule.agents = [Mock(risk_level=7), Mock(risk_level=8), Mock(risk_level=9)]
    del model.total_per_risk_level  #  reset cached property
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


def test_riskstate_str():
    # serialize as string of number for data output in batch runs
    assert str(RiskState.c1) == "1"
    assert str(RiskState.c13) == "13"


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


def test_compare_payoff():
    # test payoff fields depending on model config (recent/total)
    agent_total = HawkDoveMultipleRiskAgent(
        1,
        HawkDoveMultipleRiskModel(1, observed_neighborhood=8, adjust_payoff="total"),
        1000,
    )
    agent_total.points = 100
    agent_total.recent_points = 10

    assert agent_total.compare_payoff_field == "points"
    assert agent_total.compare_payoff == 100

    agent_recent = HawkDoveMultipleRiskAgent(
        2,
        HawkDoveMultipleRiskModel(1, observed_neighborhood=8, adjust_payoff="recent"),
        1000,
    )
    agent_recent.points = 250
    agent_recent.recent_points = 25
    assert agent_recent.compare_payoff_field == "recent_points"
    assert agent_recent.compare_payoff == 25


def test_agent_play_points():
    mock_model = HawkDoveMultipleRiskModel(3)
    agent = HawkDoveMultipleRiskAgent(1, mock_model)
    agent.points = 100
    agent.recent_points = 10

    # set initial choice and supply mock neighbors
    # so we can test expected results
    agent.choice = Play.HAWK
    neighbor_hawk = Mock(choice=Play.HAWK)
    neighbor_dove = Mock(choice=Play.DOVE)
    neighbor_dove2 = Mock(choice=Play.DOVE)
    with patch.object(
        HawkDoveMultipleRiskAgent,
        "play_neighbors",
        [neighbor_hawk, neighbor_dove, neighbor_dove2],
    ):
        agent.play()
        # should get 3*2 points against dove and 0 against the hawk
        # payoff for current round should be added to points and recent points
        assert agent.points == 106
        assert agent.recent_points == 16


def test_agent_play_adjust():
    mock_model = Mock(
        risk_adjustment="adopt", observed_neighborhood=4, max_risk_level=8
    )
    agent = HawkDoveMultipleRiskAgent(1, mock_model)
    # simulate points from previous rounds
    agent.recent_points = 250
    # simulate no neighbors to skip payoff calculation
    with patch.object(
        HawkDoveMultipleRiskAgent, "play_neighbors", new=[]
    ) as mock_adjust_risk:
        with patch.object(HawkDoveMultipleRiskAgent, "adjust_risk") as mock_adjust_risk:
            # when it is not an adjustment round, should not call adjust risk
            mock_model.adjustment_round = False
            agent.play()
            assert mock_adjust_risk.call_count == 0
            # recent points should not be reset if not an adjustment round
            assert agent.recent_points

            # should call adjust risk when the model indicates
            mock_model.adjustment_round = True
            agent.play()
            assert mock_adjust_risk.call_count == 1
            # recent points should reset on adjustment round
            assert agent.recent_points == 0


def test_adjust_risk_adopt_total():
    # initialize an agent with a mock model
    model = Mock(
        risk_adjustment="adopt",
        observed_neighborhood=4,
        max_risk_level=8,
        adjust_payoff="total",
    )
    agent = HawkDoveMultipleRiskAgent(1, model)
    # set a known risk level
    agent.risk_level = 2
    # adjust wealth as if the model had run
    agent.points = 20
    # set a mock neighbor with more points than current agent
    neighbor = HawkDoveMultipleRiskAgent(2, model)
    neighbor.risk_level = 3
    neighbor.points = 15000
    with patch.object(HawkDoveMultipleRiskAgent, "most_successful_neighbor", neighbor):
        agent.adjust_risk()
        # default behavior is to adopt successful risk level
        assert agent.risk_level == neighbor.risk_level
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


def test_adjust_risk_adopt_recent():
    # initialize an agent with a mock model
    model = Mock(
        risk_adjustment="adopt",
        observed_neighborhood=4,
        max_risk_level=8,
        adjust_payoff="recent",
    )

    agent = HawkDoveMultipleRiskAgent(1, model)
    # set a known risk level
    agent.risk_level = 2
    # adjust wealth as if the model had run
    agent.recent_points = 12
    agent.points = 3000
    # set a mock neighbor with more points than current agent
    neighbor = HawkDoveMultipleRiskAgent(2, model)
    neighbor.risk_level = 3
    neighbor.recent_points = 1500
    neighbor.points = 200
    with patch.object(HawkDoveMultipleRiskAgent, "most_successful_neighbor", neighbor):
        agent.adjust_risk()
        # default behavior is to adopt successful risk level
        assert agent.risk_level == neighbor.risk_level
        # agent should track that risk attitude was updated
        assert agent.risk_level_changed

        # now simulate a wealthiest neighbor with fewer points than current agent
        neighbor.recent_points = 12
        agent.recent_points = 5
        neighbor.risk_level = 3
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # risk level should not be changed
        assert agent.risk_level == prev_risk_level
        # agent should track that risk attitude was not changed
        assert not agent.risk_level_changed


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
    neighbor = Mock(compare_payoff=350, risk_level=3)
    with patch.object(HawkDoveMultipleRiskAgent, "most_successful_neighbor", neighbor):
        prev_risk_level = agent.risk_level
        agent.adjust_risk()
        # new risk level should be average of previous and most successful
        assert agent.risk_level == round(
            statistics.mean([neighbor.risk_level, prev_risk_level])
        )


def test_risk_level_in_bounds():
    model = HawkDoveMultipleRiskModel(3)
    for i in range(8):
        assert model._risk_level_in_bounds(i)

    assert not model._risk_level_in_bounds(-1)
    assert not model._risk_level_in_bounds(10)


def test_get_risk_attitude_generator():
    model = HawkDoveMultipleRiskModel(3)
    model.random = Mock()

    # check that the correct methods are called depending on risk distribution
    model.risk_distribution = "uniform"
    next(model.get_risk_attitude_generator())
    model.random.randint.assert_called_with(model.min_risk_level, model.max_risk_level)

    model.risk_distribution = "normal"
    model.random.gauss.return_value = 3.3  # value to convert to int
    next(model.get_risk_attitude_generator())
    model.random.gauss.assert_called_with(4.5, 1.5)

    model.risk_distribution = "skewed left"
    model.random.triangular.return_value = 2.1  # value to round
    next(model.get_risk_attitude_generator())
    model.random.triangular.assert_called_with(
        model.min_risk_level, model.max_risk_level, 0
    )

    model.risk_distribution = "skewed right"
    model.random.triangular.return_value = 7.6  # value to round
    next(model.get_risk_attitude_generator())
    model.random.triangular.assert_called_with(
        model.min_risk_level, model.max_risk_level, 9
    )

    # bimodal returns values from from two different distributions; call twice
    model.risk_distribution = "bimodal"
    model.random.gauss.return_value = 3.2
    risk_gen = model.get_risk_attitude_generator()
    next(risk_gen)
    next(risk_gen)
    model.random.gauss.assert_any_call(0, 1.5)
    model.random.gauss.assert_any_call(9, 1.5)


def test_get_risk_attitude():
    model = HawkDoveMultipleRiskModel(3)
    model.risk_attitude_generator = (x for x in [3, -1, -5, 4])
    # should return value in range as-is
    assert model.get_risk_attitude() == 3
    # values out of range should be skipped and next valid value returned
    assert model.get_risk_attitude() == 4
