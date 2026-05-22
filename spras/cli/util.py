from itertools import islice
from typing import Generator, Iterable

# Adopted from https://stackoverflow.com/a/6822773/7589775
# with a proper type signature.
def window[T](sequence: Iterable[T], n: int) -> Generator[tuple[T, ...], None, None]:
    """
    Returns a sliding window (of width n) over data from the iterable
    s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...
    """
    it = iter(sequence)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result
