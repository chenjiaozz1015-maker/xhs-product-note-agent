from app.services.content_generator import generate_note_payload


def test_rule_based_content_generation_returns_expected_structure():
    payload = generate_note_payload(
        description="便携保温杯",
        content_type="好物推荐",
        style="清新简约",
    )

    assert payload["cover_title"]
    assert payload["cover_subtitle"]
    assert len(payload["selling_points"]) == 3
    assert len(payload["note_titles"]) == 5
    assert len(payload["hashtags"]) == 10
    assert len(payload["comments"]) == 3
    assert payload["note_body"]
