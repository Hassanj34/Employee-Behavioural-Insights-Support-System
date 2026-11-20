from app.extensions import db
from app.timeutil import utcnow


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    submission_date = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    status = db.Column(db.String(32), nullable=False, default="Completed")
    workload_score = db.Column(db.Float, nullable=False)
    motivation_score = db.Column(db.Float, nullable=False)
    learning_score = db.Column(db.Float, nullable=False)
    workload_classification = db.Column(db.String(64), nullable=False)
    motivation_classification = db.Column(db.String(64), nullable=False)
    learning_classification = db.Column(db.String(64), nullable=False)

    employee = db.relationship(
        "User",
        backref=db.backref("assessments", lazy="select"),
    )
    responses = db.relationship(
        "AssessmentResponse",
        backref="assessment",
        cascade="all, delete-orphan",
    )

    def score_for(self, dimension):
        return {
            "workload": self.workload_score,
            "motivation": self.motivation_score,
            "learning": self.learning_score,
        }[dimension]

    def classification_for(self, dimension):
        return {
            "workload": self.workload_classification,
            "motivation": self.motivation_classification,
            "learning": self.learning_classification,
        }[dimension]

    def response_map(self):
        return {row.question_code: row.response_value for row in self.responses}


class AssessmentResponse(db.Model):
    __tablename__ = "assessment_responses"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False, index=True
    )
    question_code = db.Column(db.String(8), nullable=False)
    response_value = db.Column(db.Integer, nullable=False)
