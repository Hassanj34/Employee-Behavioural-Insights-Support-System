from app.services.assessment_engine import ATTENTION, DIMENSIONS, DIMENSION_LABELS

RECOMMENDATIONS = {
    ("workload", ATTENTION): "Discuss workload pressure, review priorities and clarify expectations.",
    ("workload", "Support Recommended"): "Discuss time management challenges and identify possible sources of pressure.",
    ("motivation", ATTENTION): "Discuss recognition, autonomy, workplace satisfaction and employee concerns.",
    ("motivation", "Support Recommended"): "Explore opportunities for greater involvement and recognition.",
    ("learning", ATTENTION): "Consider mentoring, additional guidance and relevant learning opportunities.",
    ("learning", "Support Recommended"): "Discuss learning challenges and identify suitable development support.",
}

MULTIPLE_ATTENTION = (
    "Arrange an individual discussion to understand the employee's overall workplace experience."
)


def recommendation_for(dimension, classification):
    return RECOMMENDATIONS.get((dimension, classification))


def recommendations_for_classifications(classifications):
    items = []
    attention_count = 0
    for dimension in DIMENSIONS:
        classification = classifications[dimension]
        text = recommendation_for(dimension, classification)
        if classification == ATTENTION:
            attention_count += 1
        if text:
            items.append(
                {
                    "dimension": dimension,
                    "label": DIMENSION_LABELS[dimension],
                    "classification": classification,
                    "text": text,
                }
            )
    if attention_count >= 2:
        items.append(
            {
                "dimension": "multiple",
                "label": "More than one area",
                "classification": ATTENTION,
                "text": MULTIPLE_ATTENTION,
            }
        )
    return items
