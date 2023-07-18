import random


def coinflip(choices: [any, any] = [0, 1], weight: float = None) -> any:
    """Flip a coin with an optional weight between 0.0 and 1.0 for the
    first choice. If no  weight is specified, a choice is made with
    equal probability.

    :param choices: list of coin flip options, defaults to [0, 1]
    :type choices: [any, any] (optional)
    :param weight: optional weight between 0.0-1.0 for the first
        choice, defaults to None
    :type weight: float (optional)

    :return: selected choice
    :rtype: any
    """
    options = {}
    if weight:
        options["weights"] = [weight, 1 - weight]
    # random.choices sorts options based on weight; return first choice
    return random.choices(choices, **options)[0]
