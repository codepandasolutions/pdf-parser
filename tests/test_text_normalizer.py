from biodata_parser.parsing.text_normalizer import normalize_text, split_lines


def test_normalize_text_collapses_common_separators() -> None:
    text = "Name | Rahul  Sharma\r\n\r\nDOB = 12/05/1994"
    normalized = normalize_text(text)

    assert "Name : Rahul Sharma" in normalized
    assert "DOB : 12/05/1994" in normalized
    assert split_lines(normalized) == ["Name : Rahul Sharma", "DOB : 12/05/1994"]
