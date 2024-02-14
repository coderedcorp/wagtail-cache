from itertools import islice


try:
    from itertools import batched  # type: ignore
except ImportError:
    # `itertools.batched` is only available from Python3.12
    # This is the equivalent code described in the Python docs.
    # https://docs.python.org/3/library/itertools.html#itertools.batched
    def batched(iterable, n):
        # batched('ABCDEFG', 3) --> ABC DEF G
        if n < 1:
            raise ValueError("n must be at least one")
        it = iter(iterable)
        while batch := tuple(islice(it, n)):
            yield batch
