from app.services.assessment_engine import (
    ATTENTION,
    POSITIVE,
    SUPPORT,
    classify,
    score_responses,
)
from app.services.recommendation_engine import recommendations_for_classifications


def test_classification_boundaries():
    assert classify(1.0) == ATTENTION
    assert classify(2.49) == ATTENTION
    assert classify(2.50) == SUPPORT
    assert classify(3.49) == SUPPORT
    assert classify(3.50) == POSITIVE
    assert classify(5.0) == POSITIVE


def test_dimensions_stay_independent():
    scores = score_responses(
        {
            "W1": 2,
            "W2": 2,
            "W3": 2,
            "W4": 2,
            "W5": 2,
            "M1": 5,
            "M2": 5,
            "M3": 4,
            "M4": 5,
            "M5": 4,
            "L1": 2,
            "L2": 2,
            "L3": 2,
            "L4": 2,
            "L5": 2,
        }
    )
    assert set(scores) == {"workload", "motivation", "learning"}
    assert scores["workload"] == 2
    assert round(scores["motivation"], 2) == 4.60
    assert scores["learning"] == 2
    assert classify(scores["workload"]) == ATTENTION
    assert classify(scores["motivation"]) == POSITIVE
    assert classify(scores["learning"]) == ATTENTION
    recommendations = recommendations_for_classifications(
        {
            "workload": ATTENTION,
            "motivation": POSITIVE,
            "learning": ATTENTION,
        }
    )
    texts = [item["text"] for item in recommendations]
    assert any("workload pressure" in text for text in texts)
    assert any("mentoring" in text for text in texts)
    assert any("individual discussion" in text for text in texts)
    assert not any("overall score" in text.lower() for text in texts)


def test_follow_up_answers_are_included_in_the_dimension_average():
    without = score_responses(
        {"W1": 4, "W2": 4, "W3": 4, "W4": 4, "W5": 4, "M1": 4, "M2": 4, "M3": 4, "M4": 4, "M5": 4, "L1": 4, "L2": 4, "L3": 4, "L4": 4, "L5": 4}
    )
    with_follow_ups = score_responses(
        {
            "W1": 4,
            "W2": 4,
            "W3": 4,
            "W4": 4,
            "W5": 4,
            "WF1": 1,
            "WF2": 1,
            "M1": 4,
            "M2": 4,
            "M3": 4,
            "M4": 4,
            "M5": 4,
            "L1": 4,
            "L2": 4,
            "L3": 4,
            "L4": 4,
            "L5": 4,
        }
    )
    assert without["workload"] == 4
    assert round(with_follow_ups["workload"], 2) == 3.14
