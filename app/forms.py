from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields.choices import SelectChoice
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp

from app.services.assessment_engine import LIKERT
from app.services.complaint_service import CATEGORIES, STATUSES

RECIPIENT_CHOICES = [
    SelectChoice("hr", "HR"),
    SelectChoice("senior_manager", "Senior Manager"),
]
FOLLOW_UP_STATUSES = ("Pending", "In Progress", "Completed")
LIKERT_CHOICES = [SelectChoice(value, label) for value, label in LIKERT]


def _radio(label):
    return RadioField(
        label,
        choices=LIKERT_CHOICES,
        validators=[DataRequired(message="This question is required."), NumberRange(min=1, max=5)],
        coerce=int,
    )


def _optional_score(value):
    if value in (None, "", "None"):
        return None
    return int(value)


def _follow_up(label):
    return RadioField(
        label,
        choices=LIKERT_CHOICES,
        validators=[Optional(), NumberRange(min=1, max=5)],
        coerce=_optional_score,
    )


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Length(max=255),
            Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message="Enter a valid email address."),
        ],
        render_kw={"autocomplete": "username", "placeholder": "name@ebiss.local"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
    submit = SubmitField("Sign in")


class AssessmentForm(FlaskForm):
    w1 = _radio("I can complete my assigned work within the expected working hours.")
    w2 = _radio("I have sufficient time to complete my responsibilities without feeling constantly rushed.")
    w3 = _radio("My current workload is manageable and does not feel overwhelming.")
    w4 = _radio("I can pause briefly during the day without falling behind.")
    w5 = _radio("Unexpected tasks are balanced against the time I already have.")
    m1 = _radio("I feel that my contributions and achievements are recognized and appreciated.")
    m2 = _radio("I have sufficient freedom and autonomy in how I perform my work.")
    m3 = _radio("I feel connected to and supported by the people I work with.")
    m4 = _radio("I can see how my work contributes to something that matters.")
    m5 = _radio("I have chances to use my skills in ways I find worthwhile.")
    l1 = _radio("I feel confident learning new skills required for my job.")
    l2 = _radio("I believe I can successfully handle new responsibilities when given appropriate guidance.")
    l3 = _radio("I feel capable of overcoming difficulties when learning unfamiliar tasks.")
    l4 = _radio("I can find the information I need when a task is unfamiliar.")
    l5 = _radio("Practice and feedback help me feel ready for a new responsibility.")
    wf1 = _follow_up("I am clear about which tasks should take priority when my workload feels high.")
    wf2 = _follow_up("I can raise workload concerns early and get a useful response.")
    mf1 = _follow_up("Recognition for my work happens often enough to keep me motivated.")
    mf2 = _follow_up("I can influence how my work is planned and carried out.")
    lf1 = _follow_up("I receive enough guidance when I am learning an unfamiliar task.")
    lf2 = _follow_up("I have access to someone who can mentor me when a new responsibility is difficult.")


class ComplaintForm(FlaskForm):
    recipient_role = SelectField(
        "Recipient",
        choices=RECIPIENT_CHOICES,
        validators=[DataRequired()],
    )
    category = SelectField(
        "Complaint category",
        choices=[SelectChoice(item, item) for item in CATEGORIES],
        validators=[DataRequired()],
    )
    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(min=3, max=200)],
    )
    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(min=10, max=5000)],
        render_kw={"rows": 6},
    )
    submit = SubmitField("Submit complaint")


class ComplaintUpdateForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[SelectChoice(item, item) for item in STATUSES],
        validators=[DataRequired()],
    )
    response_text = TextAreaField(
        "Response or resolution remark",
        validators=[DataRequired(), Length(min=3, max=5000)],
        render_kw={"rows": 4},
    )
    submit = SubmitField("Save update")


class AlertSettingsForm(FlaskForm):
    positive_min = FloatField(
        "Positive from",
        validators=[DataRequired(), NumberRange(min=1, max=5)],
    )
    support_min = FloatField(
        "Attention below",
        validators=[DataRequired(), NumberRange(min=1, max=5)],
    )
    significant_drop = FloatField(
        "Alert when a score falls by",
        validators=[DataRequired(), NumberRange(min=0.25, max=4)],
    )
    submit = SubmitField("Save alert rules")


class FollowUpForm(FlaskForm):
    action_description = TextAreaField(
        "Action taken",
        validators=[DataRequired(), Length(min=5, max=5000)],
        render_kw={"rows": 3},
    )
    remarks = TextAreaField(
        "Manager remarks",
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 3},
    )
    status = SelectField(
        "Follow-up status",
        choices=[SelectChoice(item, item) for item in FOLLOW_UP_STATUSES],
        validators=[DataRequired()],
    )
    submit = SubmitField("Record follow-up")
