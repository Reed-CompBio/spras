from spras.interval import Interval

class TestInterval:
    def test_number(self):
        assert Interval.single(5) == Interval(lower=5, upper=5, lower_closed=True, upper_closed=True)
        assert Interval.from_string("5") == Interval.single(5)
