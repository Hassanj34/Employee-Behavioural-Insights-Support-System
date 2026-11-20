"""Demonstration data for Systems Limited, Karachi."""

from datetime import datetime

from app import create_app
from app.extensions import db
from app.models.alert import Alert
from app.models.complaint import Complaint, ComplaintResponse
from app.models.follow_up import FollowUpAction
from app.models.user import User
from app.services.alert_service import save_assessment

PASSWORD = "Demo@2026"
ANCHOR_EMAIL = "imran.sheikh@systems.local"
ORGANIZATION = "Systems Limited"


def _when(day, hour=9):
    return datetime(2026, 11, day, hour, 0)


def _add_user(name, email, role, department, designation, manager=None):
    user = User(
        name=name,
        email=email,
        role=role,
        department=department,
        designation=designation,
        is_active=True,
        manager_id=manager.id if manager else None,
    )
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.flush()
    return user


def _answers(workload, motivation, learning):
    codes = ("W1", "W2", "W3", "M1", "M2", "M3", "L1", "L2", "L3")
    values = list(workload) + list(motivation) + list(learning)
    answers = dict(zip(codes, values))
    follow_ups = {
        ("W1", "W2", "W3"): ("WF1", "WF2"),
        ("M1", "M2", "M3"): ("MF1", "MF2"),
        ("L1", "L2", "L3"): ("LF1", "LF2"),
    }
    for cores, extras in follow_ups.items():
        if any(answers[code] <= 2 for code in cores):
            for extra in extras:
                answers[extra] = 2
    return answers


def _complaint(employee, recipient, category, subject, description, status, when, response_text=None):
    complaint = Complaint(
        employee_id=employee.id,
        recipient_role=recipient.role,
        recipient_id=recipient.id,
        category=category,
        subject=subject,
        description=description,
        status=status,
        created_at=when,
        updated_at=when,
    )
    db.session.add(complaint)
    db.session.flush()
    if response_text:
        db.session.add(
            ComplaintResponse(
                complaint_id=complaint.id,
                responder_id=recipient.id,
                response_text=response_text,
                created_at=when,
            )
        )
    return complaint


def seed():
    if db.session.scalars(db.select(User).where(User.email == ANCHOR_EMAIL)).first():
        print("Seed data already present. Nothing added.")
        return

    imran = _add_user(
        "Imran Sheikh",
        ANCHOR_EMAIL,
        "manager",
        "Digital Services",
        "Delivery Manager",
    )
    hira = _add_user(
        "Hira Baig",
        "hira.baig@systems.local",
        "manager",
        "Banking Solutions",
        "Delivery Manager",
    )
    nadia = _add_user(
        "Nadia Hussain",
        "nadia.hussain@systems.local",
        "hr",
        "People and Culture",
        "HR Business Partner",
    )
    zara = _add_user(
        "Zara Qureshi",
        "zara.qureshi@systems.local",
        "senior_manager",
        "Corporate Office",
        "Director, Karachi",
    )
    ayesha = _add_user(
        "Ayesha Khan",
        "ayesha.khan@systems.local",
        "employee",
        "Digital Services",
        "Software Engineer",
        imran,
    )
    bilal = _add_user(
        "Bilal Ahmed",
        "bilal.ahmed@systems.local",
        "employee",
        "Digital Services",
        "Software Engineer",
        imran,
    )
    fatima = _add_user(
        "Fatima Siddiqui",
        "fatima.siddiqui@systems.local",
        "employee",
        "Digital Services",
        "QA Engineer",
        imran,
    )
    sana = _add_user(
        "Sana Iqbal",
        "sana.iqbal@systems.local",
        "employee",
        "Digital Services",
        "Business Analyst",
        imran,
    )
    saad = _add_user(
        "Saad Malik",
        "saad.malik@systems.local",
        "employee",
        "Banking Solutions",
        "Associate Engineer",
        hira,
    )
    db.session.commit()

    save_assessment(ayesha, _answers((4, 4, 4), (4, 4, 4), (4, 4, 4)), _when(6))
    save_assessment(ayesha, _answers((4, 5, 4), (5, 4, 4), (4, 4, 5)), _when(13))
    save_assessment(ayesha, _answers((5, 4, 5), (4, 5, 5), (5, 4, 5)), _when(18))

    save_assessment(bilal, _answers((1, 2, 1), (4, 5, 4), (4, 4, 5)), _when(5))
    save_assessment(bilal, _answers((2, 2, 2), (4, 4, 5), (5, 4, 4)), _when(12))
    save_assessment(bilal, _answers((2, 2, 3), (5, 4, 4), (4, 5, 4)), _when(18, 11))

    save_assessment(fatima, _answers((4, 4, 4), (1, 2, 2), (4, 5, 4)), _when(8))
    save_assessment(fatima, _answers((4, 5, 4), (2, 2, 2), (4, 4, 4)), _when(17))

    save_assessment(sana, _answers((4, 5, 4), (5, 5, 4), (4, 4, 5)), _when(7))
    save_assessment(sana, _answers((4, 4, 5), (3, 3, 4), (4, 5, 4)), _when(18, 15))

    save_assessment(saad, _answers((4, 4, 5), (4, 5, 4), (2, 2, 2)), _when(7))
    save_assessment(saad, _answers((5, 4, 4), (4, 4, 5), (4, 4, 5)), _when(16))

    workload_alert = db.session.scalars(
        db.select(Alert)
        .where(Alert.employee_id == bilal.id, Alert.dimension == "Workload")
        .order_by(Alert.created_at.asc())
    ).first()
    workload_alert.status = "In Progress"
    db.session.add(
        FollowUpAction(
            alert_id=workload_alert.id,
            manager_id=imran.id,
            action_description="Discussed the Karachi release deadlines and moved two non-critical tasks off Bilal's week.",
            remarks="Bilal will raise workload pressure before the next sprint planning.",
            status="In Progress",
            usefulness="Partly useful",
            usefulness_note="The next check-in is still in the attention range, so the change in deadlines has not been enough yet.",
            reviewed_at=_when(13, 10),
            created_at=_when(6, 15),
            updated_at=_when(13, 10),
        )
    )

    motivation_alert = db.session.scalars(
        db.select(Alert)
        .where(Alert.employee_id == fatima.id, Alert.dimension == "Motivation")
        .order_by(Alert.created_at.asc())
    ).first()
    motivation_alert.status = "Completed"
    db.session.add(
        FollowUpAction(
            alert_id=motivation_alert.id,
            manager_id=imran.id,
            action_description="Held a recognition conversation and agreed a weekly one-to-one.",
            remarks="Fatima asked for clearer ownership of the regression suite.",
            status="Completed",
            usefulness="Useful",
            usefulness_note="Fatima said the weekly one-to-one made it easier to raise concerns about recognition.",
            reviewed_at=_when(18, 9),
            created_at=_when(9, 14),
            updated_at=_when(18, 9),
        )
    )

    _complaint(
        ayesha,
        nadia,
        "Promotion or Career Progression",
        "Promotion timeline for the digital team",
        "I would like People and Culture to review the timeline and criteria used for the last promotion round in Digital Services.",
        "Under Review",
        _when(18, 10),
        "We have received this and are reviewing the promotion timeline with your delivery manager.",
    )
    _complaint(
        bilal,
        zara,
        "Project or Role Assignment",
        "Release role does not match the agreed scope",
        "The current release assignment in Karachi does not match the responsibilities we discussed at the start of the quarter.",
        "Submitted",
        _when(15, 10),
    )
    _complaint(
        fatima,
        nadia,
        "Workplace Treatment",
        "Sprint review comments",
        "Recent sprint reviews have included comments that made it difficult to raise quality concerns.",
        "Resolved",
        _when(11, 16),
        "We spoke with the people involved and agreed how feedback will be given in sprint reviews.",
    )
    _complaint(
        saad,
        zara,
        "Recognition or Fairness",
        "Recognition for the banking release",
        "The banking release work was completed, and I would like that contribution to be acknowledged fairly.",
        "Closed",
        _when(10, 12),
        "A recognition note has been shared with your delivery manager.",
    )
    db.session.commit()
    print(f"Seed data created for {ORGANIZATION}, Karachi.")
    print("Password for every demonstration account: Demo@2026")


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        seed()
