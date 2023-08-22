import random


def coinflip(choices: [any, any] = [0, 1], weight: float = 0.5) -> any:
    """Flip a coin with an optional weight between 0.0 and 1.0 for the
    first choice. If no  weight is specified, a choice is made with
    equal probability.

    :param choices: list of coin flip options, defaults to [0, 1]
    :type choices: [any, any] (optional)
    :param weight: optional weight between 0.0-1.0 for the first
        choice, defaults to 0.5
    :type weight: float (optional)

    :return: selected choice
    :rtype: any
    """
    # adapted from https://stackoverflow.com/a/477248/9706217
    # random.random is apparently faster than
    selection = 0 if random.random() < weight else 1
    return choices[selection]


def labelLabel(fields):
    # some kind of a bug in current (forked) version of Mesa or
    # a conflict with tornado version on field labels;
    # display is undefined without lowercase but server requires uppercase
    # for now, just copy them
    for item in fields:
        item["label"] = item["Label"]
    return fields
