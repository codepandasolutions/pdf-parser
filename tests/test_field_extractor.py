from biodata_parser.parsing.field_extractor import extract_fields


def test_extract_fields_uses_labels_and_regex() -> None:
    config = [
        {
            "key": "full_name",
            "labels": ["name"],
            "type": "string",
            "required": True,
            "confidence": {"label_match": 0.9},
        },
        {
            "key": "contact_number",
            "labels": ["mobile"],
            "type": "phone",
            "regex_patterns": [r"(?:\+91[-\s]?)?[6-9]\d{9}"],
            "confidence": {"regex_match": 0.7},
        },
    ]
    result = extract_fields("Name: Rahul Sharma\nMobile: 9876543210", config)

    assert result["values"]["full_name"] == "Rahul Sharma"
    assert result["values"]["contact_number"] == "9876543210"
    assert result["overall_confidence"] > 0


def test_extract_fields_supports_next_line_value() -> None:
    config = [
        {
            "key": "full_name",
            "labels": ["name"],
            "type": "string",
            "required": True,
            "confidence": {"label_match": 0.9},
        }
    ]

    result = extract_fields("Name\nRahul Sharma\nEducation\nB.Tech", config)

    assert result["values"]["full_name"] == "Rahul Sharma"


def test_extract_fields_multiline_stops_at_next_label() -> None:
    config = [
        {
            "key": "address",
            "labels": ["address"],
            "type": "string",
            "multiline": True,
            "max_lines": 4,
            "stop_at_next_label": True,
            "confidence": {"label_match": 0.9},
        },
        {
            "key": "education",
            "labels": ["education"],
            "type": "string",
            "confidence": {"label_match": 0.9},
        },
    ]

    result = extract_fields("Address\nLine 1\nLine 2\nEducation: B.Tech", config)

    assert result["values"]["address"] == "Line 1 Line 2"
    assert result["values"]["education"] == "B.Tech"
