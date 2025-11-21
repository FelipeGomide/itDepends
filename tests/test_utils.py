from datetime import datetime
from itdepends import utils

def test_diff_in_months_same_month():
    d1 = datetime(2024, 5, 10)
    d2 = datetime(2024, 5, 20)

    assert utils.diff_in_months(d1, d2) == 0


def test_diff_in_months_multiple_months():
    d1 = datetime(2023, 1, 1)
    d2 = datetime(2024, 4, 1)

    assert utils.diff_in_months(d1, d2) == 15


def test_diff_in_months_negative():
    d1 = datetime(2024, 5, 1)
    d2 = datetime(2024, 2, 1)

    assert utils.diff_in_months(d1, d2) == -3
