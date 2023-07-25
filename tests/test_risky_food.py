from collections import Counter
import math
from unittest.mock import Mock, patch, PropertyMock

import pytest

from simulatingrisk.risky_food.model import (
    RiskyFoodModel,
    FoodStatus,
    FoodChoice,
    Agent,
)


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


def test_agent_init():
    model = RiskyFoodModel(1)
    agent_id = 123
    agent = Agent(agent_id, model)
    assert agent.model == model
    assert agent.unique_id == agent_id
    # random risk level
    assert agent.risk_level >= 0.0 and agent.risk_level <= 1.0

    # assigned risk level
    risk = 0.4
    agent2 = Agent(1, model, risk_level=risk)
    assert agent2.risk_level == risk

    # allow zero risk (should not get a random value)
    agent0 = Agent(1, model, risk_level=0)
    assert agent0.risk_level == 0


def test_agent_step():
    model = RiskyFoodModel(1)
    agent = model.schedule.agents[0]
    # if risk level is lower than probability not contaminated, agent will risk
    agent.risk_level = 0.2
    model.prob_notcontaminated = 0.3
    model.risky_food_status = FoodStatus.CONTAMINATED
    agent.step()
    assert agent.choice == FoodChoice.RISKY

    # if not strictly higher, no risk
    model.prob_notcontaminated = 0.2
    agent.step()
    assert agent.choice == FoodChoice.SAFE

    # risk level 1.0 == always chooses safe
    agent.risk_level = 1.0
    model.prob_notcontaminated = 0.99
    agent.step()
    assert agent.choice == FoodChoice.SAFE


def test_propagate_types():
    model = RiskyFoodModel(mode="types")
    # patch in schedule and agents by risk type
    model.schedule = Mock()
    with patch.object(
        RiskyFoodModel, "agents_by_risktype", new_callable=PropertyMock
    ) as mock_agents_by_rtype:
        # simulate safe payoff (2)
        mock_agents_by_rtype.return_value = {
            0.3: [Mock(payoff=2), Mock(), Mock(), Mock()]
        }
        model.propagate_types()
        # total should stay the same; no agents removed or added
        model.schedule.remove.assert_not_called()
        model.schedule.add.assert_not_called()

        # simulate contaminated food payoff (1)
        mock_agents_by_rtype.return_value = {
            0.2: [Mock(payoff=1), Mock(), Mock(), Mock()]
        }
        model.schedule.reset_mock()
        model.propagate_types()
        # population should be cut in half; should remove two agents
        assert model.schedule.remove.call_count == 2
        model.schedule.add.assert_not_called()

        # simulate non-contaminated risky food payoff (4)
        mock_agents_by_rtype.return_value = {
            0.6: [Mock(payoff=4), Mock(), Mock(), Mock()]
        }
        model.schedule.reset_mock()
        model.propagate_types()
        # population should double; should add four agents
        assert model.schedule.add.call_count == 4
        model.schedule.remove.assert_not_called()
