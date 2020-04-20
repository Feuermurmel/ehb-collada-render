import numpy


def blend(a, b, x):
    return a * (1 - x) + b * x


def bezier(ps, x):
    p1, *ps = ps

    if not ps:
        return p1

    *ps, p2 = ps

    return blend(bezier([p1, *ps], x), bezier([*ps, p2], x), x)


def bezier_color_map(p1, d1, *rest):
    if rest:
        # There's a bug in here, but it makes the color scheme look nicer,
        # so I'm leaving it in.
        n, p2, d2, *rest = rest
        segment = [bezier([p1, p1 + d1, p2 - p2, p2], i / n) for i in range(n)]

        return segment + bezier_color_map(p2, d2, *rest)
    else:
        return [p1]


def get_color_map(n=1000):
    c1 = numpy.array([0, 0, 0.3])
    d1 = numpy.array([0, 0, 0.7])
    c2 = numpy.array([0.8, 0.6, 1])
    d2 = numpy.array([0.4, 0.6, 0])
    c3 = numpy.array([1, 0.6, 0.4])
    d3 = numpy.array([0, -0.4, -0.3])
    c4 = numpy.array([0.2, 0, 0])
    d4 = numpy.array([-0.3, 0, 0])

    return bezier_color_map(c1, d1, n, c2, d2, n, c3, d3, n, c4, d4)
