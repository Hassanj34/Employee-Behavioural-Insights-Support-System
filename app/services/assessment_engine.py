"""Transparent, rule-based scoring for the three assessment dimensions.

Scores are independent. This module never produces a combined employee score.
"""

DIMENSIONS = ("workload", "motivation", "learning")

DIMENSION_LABELS = {
    "workload": "Workload",
    "motivation": "Motivation",
    "learning": "Learning Confidence",
}

SECTION_NOTES = {
    "workload": (
        "Self-reported workload manageability and time pressure. "
        "Source: Karasek, R., & Theorell, T. (1990). Healthy Work: Stress, Productivity, and the Reconstruction of Working Life. Basic Books."
    ),
    "motivation": (
        "Recognition, autonomy, and relatedness, drawing on Herzberg's Two-Factor Theory and Self-Determination Theory. "
        "Sources: Herzberg, F., Mausner, B., & Snyderman, B. B. (1959). The Motivation to Work. John Wiley; "
        "Deci, E. L., & Ryan, R. M. (2000). The \"what\" and \"why\" of goal pursuits: Human needs and the self-determination of behavior. Psychological Inquiry, 11(4), 227–268."
    ),
    "learning": (
        "Confidence to learn and handle new responsibilities, drawing on Social Cognitive Theory. "
        "Source: Bandura, A. (1997). Self-efficacy: The Exercise of Control. W. H. Freeman."
    ),
}

QUESTIONS = [
    {
        "code": "W1",
        "dimension": "workload",
        "text": "I can complete my assigned work within the expected working hours.",
    },
    {
        "code": "W2",
        "dimension": "workload",
        "text": "I have sufficient time to complete my responsibilities without feeling constantly rushed.",
    },
    {
        "code": "W3",
        "dimension": "workload",
        "text": "My current workload is manageable and does not feel overwhelming.",
    },
    {
        "code": "W4",
        "dimension": "workload",
        "text": "I can pause briefly during the day without falling behind.",
    },
    {
        "code": "W5",
        "dimension": "workload",
        "text": "Unexpected tasks are balanced against the time I already have.",
    },
    {
        "code": "M1",
        "dimension": "motivation",
        "text": "I feel that my contributions and achievements are recognized and appreciated.",
    },
    {
        "code": "M2",
        "dimension": "motivation",
        "text": "I have sufficient freedom and autonomy in how I perform my work.",
    },
    {
        "code": "M3",
        "dimension": "motivation",
        "text": "I feel connected to and supported by the people I work with.",
    },
    {
        "code": "M4",
        "dimension": "motivation",
        "text": "I can see how my work contributes to something that matters.",
    },
    {
        "code": "M5",
        "dimension": "motivation",
        "text": "I have chances to use my skills in ways I find worthwhile.",
    },
    {
        "code": "L1",
        "dimension": "learning",
        "text": "I feel confident learning new skills required for my job.",
    },
    {
        "code": "L2",
        "dimension": "learning",
        "text": "I believe I can successfully handle new responsibilities when given appropriate guidance.",
    },
    {
        "code": "L3",
        "dimension": "learning",
        "text": "I feel capable of overcoming difficulties when learning unfamiliar tasks.",
    },
    {
        "code": "L4",
        "dimension": "learning",
        "text": "I can find the information I need when a task is unfamiliar.",
    },
    {
        "code": "L5",
        "dimension": "learning",
        "text": "Practice and feedback help me feel ready for a new responsibility.",
    },
    {
        "code": "WF1",
        "dimension": "workload",
        "follow_up": True,
        "text": "I am clear about which tasks should take priority when my workload feels high.",
    },
    {
        "code": "WF2",
        "dimension": "workload",
        "follow_up": True,
        "text": "I can raise workload concerns early and get a useful response.",
    },
    {
        "code": "MF1",
        "dimension": "motivation",
        "follow_up": True,
        "text": "Recognition for my work happens often enough to keep me motivated.",
    },
    {
        "code": "MF2",
        "dimension": "motivation",
        "follow_up": True,
        "text": "I can influence how my work is planned and carried out.",
    },
    {
        "code": "LF1",
        "dimension": "learning",
        "follow_up": True,
        "text": "I receive enough guidance when I am learning an unfamiliar task.",
    },
    {
        "code": "LF2",
        "dimension": "learning",
        "follow_up": True,
        "text": "I have access to someone who can mentor me when a new responsibility is difficult.",
    },
]

QUESTION_BY_CODE = {question["code"]: question for question in QUESTIONS}
CORE_CODES = [question["code"] for question in QUESTIONS if not question.get("follow_up")]
CODES_BY_DIMENSION = {
    dimension: [code for code in CORE_CODES if QUESTION_BY_CODE[code]["dimension"] == dimension]
    for dimension in DIMENSIONS
}
FOLLOW_UPS_BY_DIMENSION = {
    dimension: [question["code"] for question in QUESTIONS if question.get("follow_up") and question["dimension"] == dimension]
    for dimension in DIMENSIONS
}

LIKERT = (
    (1, "Strongly Disagree"),
    (2, "Disagree"),
    (3, "Neutral"),
    (4, "Agree"),
    (5, "Strongly Agree"),
)
LIKERT_LABELS = dict(LIKERT)

POSITIVE = "Positive / Balanced"
SUPPORT = "Support Recommended"
ATTENTION = "Attention Required"
INSUFFICIENT = "Insufficient Data"
SIGNIFICANT = "Significant Change"

CONCERN_PHRASES = {
    "W1": "completing assigned work within expected working hours",
    "W2": "having enough time without feeling constantly rushed",
    "W3": "keeping the current workload manageable",
    "W4": "being able to pause briefly without falling behind",
    "W5": "balancing unexpected tasks with the time already available",
    "M1": "feeling that contributions are recognized",
    "M2": "having enough autonomy in how the work is done",
    "M3": "feeling connected to and supported by colleagues",
    "M4": "seeing how the work contributes to something that matters",
    "M5": "chances to use skills in worthwhile ways",
    "L1": "confidence in learning new skills required for the job",
    "L2": "belief in handling new responsibilities when guidance is available",
    "L3": "feeling capable of overcoming difficulties with unfamiliar tasks",
    "L4": "finding information when a task is unfamiliar",
    "L5": "feeling ready for a new responsibility after practice and feedback",
    "WF1": "clarity about which tasks should take priority",
    "WF2": "being able to raise workload concerns early",
    "MF1": "how often work is recognized",
    "MF2": "influence over how work is planned",
    "LF1": "guidance while learning an unfamiliar task",
    "LF2": "access to mentoring for a difficult new responsibility",
}


def questions_for_dimension(dimension):
    return [question for question in QUESTIONS if question["dimension"] == dimension]


def triggered_follow_ups(core):
    required = []
    for dimension, codes in CODES_BY_DIMENSION.items():
        if any(core[code] <= 2 for code in codes):
            required.extend(FOLLOW_UPS_BY_DIMENSION[dimension])
    return required


def classify(score, positive_min=3.50, support_min=2.50):
    if score is None:
        return INSUFFICIENT
    if score >= positive_min:
        return POSITIVE
    if score >= support_min:
        return SUPPORT
    if 1.00 <= score < support_min:
        return ATTENTION
    return INSUFFICIENT


def classification_key(label):
    return {
        POSITIVE: "positive",
        SUPPORT: "support",
        ATTENTION: "attention",
        INSUFFICIENT: "insufficient",
        SIGNIFICANT: "change",
    }.get(label, "insufficient")


def _clean_code(code, value):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Each response must be a whole number from 1 to 5.") from exc
    if number < 1 or number > 5:
        raise ValueError("Each response must be a whole number from 1 to 5.")
    return number


def core_map(responses):
    missing = [code for code in CORE_CODES if code not in responses]
    if missing:
        raise ValueError("All fifteen core questions are required.")
    return {code: _clean_code(code, responses[code]) for code in CORE_CODES}


def validate_responses(responses):
    core = core_map(responses)
    cleaned = dict(core)
    for code in triggered_follow_ups(core):
        if code not in responses or responses[code] in (None, ""):
            raise ValueError("Answer the follow-up questions for any area you disagreed with.")
        cleaned[code] = _clean_code(code, responses[code])
    return cleaned


def score_responses(responses):
    """Average the five core answers, plus any follow-up answers that were shown."""
    core = core_map(responses)
    scores = {}
    for dimension, codes in CODES_BY_DIMENSION.items():
        values = [core[code] for code in codes]
        for code in FOLLOW_UPS_BY_DIMENSION[dimension]:
            raw = responses.get(code)
            if raw in (None, ""):
                continue
            values.append(_clean_code(code, raw))
        scores[dimension] = sum(values) / len(values)
    return scores


def _join(phrases):
    phrases = list(phrases)
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    return ", ".join(phrases[:-1]) + " and " + phrases[-1]


def explain(dimension, responses, classification, audience="employee"):
    label = DIMENSION_LABELS[dimension].lower()
    codes = CODES_BY_DIMENSION[dimension]
    low_codes = [code for code in codes if code in responses and int(responses[code]) <= 2]
    mild_codes = [code for code in codes if code in responses and int(responses[code]) == 3]
    focus = low_codes or mild_codes
    follow_low = [
        code
        for code in FOLLOW_UPS_BY_DIMENSION[dimension]
        if code in responses and int(responses[code]) <= 2
    ]
    details = _join(CONCERN_PHRASES[code] for code in list(focus) + follow_low)

    if classification == POSITIVE:
        if audience == "manager":
            return (
                f"The employee's responses on {label} are in a positive range. "
                "No urgent support signal was generated for this dimension. "
                "This reading is based on self-reported responses, not a performance rating."
            )
        return (
            f"Your responses suggest that {label} is in a positive range right now. "
            "This indicator is based only on what you reported in this check-in."
        )

    if classification == ATTENTION:
        employee_lead = f"Your responses indicate that {label} may need attention"
        manager_lead = f"Employee responses on {label} indicate a need for attention"
    else:
        employee_lead = f"Your responses suggest that a conversation about {label} could be useful"
        manager_lead = f"Employee responses on {label} suggest that some support may help"

    if audience == "manager":
        sentence = manager_lead
        if details:
            sentence += f", particularly around {details}"
        return (
            sentence + ". "
            "This classification is based on self-reported responses and is a prompt for a supportive conversation, "
            "not a diagnosis or an employment decision."
        )

    sentence = employee_lead
    if details:
        sentence += f", especially {details}"
    return (
        sentence + ". "
        "Consider discussing this with your manager. "
        "This indicator is based only on your self-reported responses. "
        "It is not a psychological diagnosis or a performance rating."
    )


def present_indicators(assessment, audience):
    responses = assessment.response_map()
    items = []
    for dimension in DIMENSIONS:
        classification = assessment.classification_for(dimension)
        items.append(
            {
                "key": dimension,
                "label": DIMENSION_LABELS[dimension],
                "score": assessment.score_for(dimension),
                "classification": classification,
                "explanation": explain(dimension, responses, classification, audience),
            }
        )
    return items


def chart_payload(assessments):
    ordered = sorted(assessments, key=lambda row: (row.submission_date, row.id))
    return {
        "labels": [row.submission_date.strftime("%d %b") for row in ordered],
        "workload": [round(row.workload_score, 2) for row in ordered],
        "motivation": [round(row.motivation_score, 2) for row in ordered],
        "learning": [round(row.learning_score, 2) for row in ordered],
    }


def history_for(employee_id, start=None, before=None):
    from app.extensions import db
    from app.models.assessment import Assessment

    statement = db.select(Assessment).where(Assessment.employee_id == employee_id)
    if start is not None:
        statement = statement.where(Assessment.submission_date >= start)
    if before is not None:
        statement = statement.where(Assessment.submission_date < before)
    return db.session.scalars(
        statement.order_by(Assessment.submission_date.asc(), Assessment.id.asc())
    ).all()


def latest_for(employee_id, start=None, before=None):
    if start is None and before is None:
        from app.extensions import db
        from app.models.assessment import Assessment

        return db.session.scalars(
            db.select(Assessment)
            .where(Assessment.employee_id == employee_id)
            .order_by(Assessment.submission_date.desc(), Assessment.id.desc())
        ).first()
    records = history_for(employee_id, start, before)
    return records[-1] if records else None
