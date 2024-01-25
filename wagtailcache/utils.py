from itertools import islice
from typing import Any
from typing import Generator


# `itertools.batched` is only available from Python3.12
# This is a simplified version of the equivalent code described
# in the Python docs.
# https://docs.python.org/3/library/itertools.html#itertools.batched
def batched(iterable, batch_size: int) -> Generator[tuple, Any, None]:
    # batched('ABCDEFG', 3) --> ABC DEF G
    if batch_size < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, batch_size)):
        yield batch
