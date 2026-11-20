ROLE_LABELS = {
    "employee": "Employee",
    "manager": "Manager",
    "hr": "HR Representative",
    "senior_manager": "Senior Manager",
}

RECIPIENT_LABELS = {
    "hr": "HR",
    "senior_manager": "Senior Manager",
}

DASHBOARD_ENDPOINTS = {
    "employee": "employee.dashboard",
    "manager": "manager.dashboard",
    "hr": "hr.dashboard",
    "senior_manager": "senior_manager.dashboard",
}


def status_key(value):
    return {
        "Submitted": "support",
        "Under Review": "attention",
        "Resolved": "positive",
        "Closed": "insufficient",
        "Open": "attention",
        "In Progress": "support",
        "Pending": "support",
        "Completed": "positive",
    }.get(value, "insufficient")


def initials(name):
    parts = [part for part in (name or "").split() if part]
    letters = "".join(part[0] for part in parts[:2])
    return letters.upper() or "EB"
