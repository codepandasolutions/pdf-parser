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
