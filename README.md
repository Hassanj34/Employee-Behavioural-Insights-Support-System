# Solace

A Flask application that helps a manager notice workload, motivation, and learning-confidence signals early, then follow up with a conversation. Employees complete a short check-in. A transparent rule engine classifies each area separately and opens an alert when support is needed or a score drops sharply. Complaints go to HR or a Senior Manager and stay separate from check-ins.

This is a support tool for a course prototype. It does not rank employees, diagnose anyone, or make employment decisions.

## Features

- Four roles: Employee, Manager, HR, and Senior Manager. Access is enforced on the server.
- A fifteen-question check-in, five questions in each area, with extra follow-up questions when someone disagrees with a core item. Follow-up answers count in that area's score.
- Separate scores for workload, motivation, and learning confidence, each with a plain-language explanation.
- Manager alerts, suggested conversations, and a record of whether a follow-up was useful.
- Configurable alert rules for the Senior Manager. Stored check-ins keep the classification they had when they were submitted.
- Employee complaints with status tracking. HR and the Senior Manager each see only the complaints addressed to them.
- Search, filters, date ranges, charts, and printable summaries.
- A seeded demonstration company, Systems Limited in Karachi, so the app can be shown immediately after setup.

## Tech stack

| Piece | What it is |
|---|---|
| Python 3.12 or newer | The only runtime you need to install |
| Flask 3 | Web application |
| Flask-SQLAlchemy and SQLite | Database. SQLite ships with Python |
| Flask-Login | Sign-in and sessions |
| Flask-WTF | Forms and CSRF protection |
| pytest | Automated tests |
| Bootstrap 5, Bootstrap Icons, Chart.js | Interface and charts, stored in `app/static/vendor/` |

No Node.js install, no separate database server, and no network connection after the Python packages are installed. The pages load their CSS and JavaScript from the repository.

## Prerequisites

Install these two tools, then confirm both commands print a version:

1. [Python 3.12 or newer](https://www.python.org/downloads/). On Windows, tick **Add python.exe to PATH** in the installer. On macOS, `python3` from [python.org](https://www.python.org/downloads/) is the reliable choice. On Linux, use your distribution's `python3` and `python3-venv` packages.
2. [Git](https://git-scm.com/downloads).

```text
python --version
git --version
```

If `python` is not found, try `python3`. Use that name in every command below.

## Setup

Clone the repository and move into the project folder:

```bash
git clone https://github.com/Hassanj34/Employee-Behavioural-Insights-Support-System.git
cd Employee-Behavioural-Insights-Support-System
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If activation is blocked, allow scripts for the current window only and run the activate command again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Secret key

A development `.env` is included in the repository, so the app can start after the packages are installed. `SECRET_KEY` in that file is for this local demonstration. Replace it before using the application anywhere other than your own machine. If `.env` is missing, copy `.env.example` to `.env` first.

You can generate a new value with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Leave `FLASK_DEBUG=1` while you are running the demonstration locally. The app listens on your own computer only.

## Run the demonstration

The virtual environment prompt should still be active (`(.venv)` at the start of the line). Create the demonstration records, then start the server:

```bash
python seed_data.py
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

`seed_data.py` is safe to run again. If the demonstration accounts already exist, it leaves the database unchanged. Starting the app creates any missing tables and does not delete `instance/application.db`.

To start over, stop the server with `Ctrl+C`, delete `instance/application.db`, and run `python seed_data.py` again.

## Accounts

Every seeded account uses the password `Demo@2026`. Sign in with the email and that password.

The organization is Systems Limited, Karachi. The people are demonstration accounts.

| Name | Email | Role |
|---|---|---|
| Ayesha Khan | ayesha.khan@systems.local | Employee, balanced history. Manager: Imran Sheikh |
| Bilal Ahmed | bilal.ahmed@systems.local | Employee, workload pressure. Manager: Imran Sheikh |
| Fatima Siddiqui | fatima.siddiqui@systems.local | Employee, low motivation. Manager: Imran Sheikh |
| Sana Iqbal | sana.iqbal@systems.local | Employee, motivation drop that stays above the attention line. Manager: Imran Sheikh |
| Saad Malik | saad.malik@systems.local | Employee, learning confidence that later improves. Manager: Hira Baig |
| Imran Sheikh | imran.sheikh@systems.local | Delivery Manager, Digital Services |
| Hira Baig | hira.baig@systems.local | Delivery Manager, Banking Solutions |
| Nadia Hussain | nadia.hussain@systems.local | HR Business Partner |
| Zara Qureshi | zara.qureshi@systems.local | Director. Owns the alert rules |

## Walkthrough

1. Sign in as `bilal.ahmed@systems.local`.
2. Open **New Check-in** and answer all fifteen questions. Disagreeing with a core question reveals two follow-up questions for that area, and those answers count in the area score.
3. Submit the check-in and read the three indicators. Each area has its own score, classification, and explanation.
4. Sign out and sign in as `imran.sheikh@systems.local`.
5. Open Bilal Ahmed and his workload alert. Read the explanation and the suggested conversation.
6. Record a follow-up, then mark it Useful, Partly useful, or Not useful.
7. Open **Alerts** and filter by **Significant Change**. Sana Iqbal's motivation fell from 4.40 to 3.60, so an alert exists even though the new score is above the attention line.
8. Sign back in as Bilal Ahmed, submit a second check-in, and open **Check-in History**. Both submissions appear on the chart.
9. Submit a workplace complaint addressed to HR.
10. Sign in as `nadia.hussain@systems.local`, open that complaint, add a remark, and set the status to Under Review.
11. Sign back in as Bilal Ahmed and confirm the new status on **My Complaints**.
12. Sign in as Imran Sheikh and try to open the HR complaint. Access is refused, and the complaint text is not shown.
13. Sign in as `zara.qureshi@systems.local` and open **Alert Rules**. Change a threshold and save it. The new rule applies to check-ins submitted after the save.

Two boundaries worth showing: Hira Baig cannot open Imran Sheikh's employees, and HR cannot open a complaint sent to the Director.

## How the indicators are calculated

Each area is the average of its five core answers on a 1–5 scale. The questions are positively worded, so a higher number is a more positive experience. If any core answer in an area is Disagree or Strongly Disagree, two follow-up answers are required and included in that same average. There is no combined employee score.

The starting rules are:

| Score | Classification | Alert |
|---|---|---|
| 3.50–5.00 | Positive / Balanced | No |
| 2.50–3.49 | Support Recommended | No, unless the score fell sharply |
| 1.00–2.49 | Attention Required | Yes, for the employee's manager |
| Drop of 0.75 or more from the previous check-in | Significant Change | Yes, even when the new score stays above the attention line |

The Director can change the positive line, the attention line, and the drop size under **Alert Rules**. A first check-in that is only Support Recommended does not open an alert, because there is no earlier score to compare. These cut-offs are prototype defaults for the demonstration. They are not diagnostic thresholds.

The workload items draw on Karasek and Theorell. The motivation items draw on Herzberg's Two-Factor Theory and Self-Determination Theory. The learning-confidence items draw on Bandura's Social Cognitive Theory. Each section of the check-in names its source.

## Tests

With the virtual environment active:

```bash
python -m pytest
```

The tests use an in-memory database. They do not read or change `instance/application.db`.

## Project layout

```text
app/                  Application code, templates, and static files
app/static/vendor/    Bootstrap, Bootstrap Icons, and Chart.js
instance/             SQLite database, created locally and not committed
tests/                pytest suite
config.py             Configuration and environment variables
seed_data.py          Demonstration accounts and history
run.py                Local development server
requirements.txt      Pinned Python packages
.env.example          Variables to copy into .env
```

## Configuration

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs the session cookie. The committed value is for local demonstration. |
| `FLASK_DEBUG` | `1` reloads the server when code changes. Use `0` if you do not want debug mode. |
| `DATABASE_URL` | Optional. When omitted, the app uses `instance/application.db`. |

## Out of scope

Public registration, email or SMS notifications, anonymous complaints, task assignment, workload scheduling, peer rankings, organization-wide benchmarking, and predictive analytics are not part of this prototype.
