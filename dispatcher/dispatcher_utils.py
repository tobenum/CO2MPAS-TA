__author__ = 'Vincenzo Arcidiacono'


def dispatch(dsp, kwargs_inputs, outputs):
    return dsp.dispatch(kwargs_inputs, outputs, shrink=True)[1]


def combine(*args):
    d = dict(args[0])
    for a in args[1:]:
        d.update(a)
    return d


def bypass(*args):
    return args if len(args) > 1 else args[0]


def summation(*args):
    return sum(args)


def grouping(*args):
    return tuple(args)

