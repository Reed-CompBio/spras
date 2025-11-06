from spras.interval import Interval


class TestInterval:
    def test_number(self):
        assert Interval.single(5) == Interval(lower=5, upper=5, lower_closed=True, upper_closed=True)
        assert Interval.from_string("5") == Interval.single(5)

    def test_string_permutations(self):
        assert Interval.from_string("<5") == Interval.from_string("<  5")
        assert Interval.from_string("5<") == Interval.from_string("5 < x")
        assert Interval.from_string("6<") == Interval.from_string("x > 6")
        assert Interval.from_string("100 <") == Interval.from_string(">100")
        assert Interval.from_string("200 >= x > 100") == Interval.from_string("100 < x <= 200")

    def test_orientation(self):
        assert Interval.from_string("10<").upper is None
        assert Interval.from_string("10<").lower == 10.0
