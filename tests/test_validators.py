from biodata_parser.parsing.validators import clean_value_for_type


def test_phone_cleanup() -> None:
    assert clean_value_for_type("+91 98765 43210", "phone") == "+919876543210"


def test_date_cleanup() -> None:
    assert clean_value_for_type("12/05/1994", "date") == "1994-05-12"


def test_date_cleanup_handles_named_months() -> None:
    assert clean_value_for_type("12th May 1994", "date") == "1994-05-12"


def test_date_cleanup_handles_iso_dates() -> None:
    assert clean_value_for_type("1994-05-12", "date") == "1994-05-12"


def test_date_cleanup_handles_joined_month_values() -> None:
    assert clean_value_for_type("9thJuly, 1997", "date") == "1997-07-09"
