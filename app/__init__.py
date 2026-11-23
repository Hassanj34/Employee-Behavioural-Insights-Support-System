from flask import Flask, render_template
from flask_login import current_user

from app.extensions import csrf, db, login_manager
from app.labels import RECIPIENT_LABELS, ROLE_LABELS, initials, status_key
from app.query_filters import ALERT_STATUSES, CLASSIFICATIONS, COMPLAINT_STATUSES, DIMENSION_CHOICES
from app.services.assessment_engine import SIGNIFICANT, classification_key
from config import Config


def _add_notification_cleared_column():
    """Keep databases created before cleared notifications had that column."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "notifications" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("notifications")}
    if "cleared_at" in columns or "kind" in columns:
        return
    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE notifications ADD COLUMN cleared_at DATETIME"))


def _migrate_notifications():
    """Replace alert-only notifications with a table that can describe any event."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "notifications" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("notifications")}
    if "kind" in columns and "summary" in columns and "href" in columns:
        return
    with db.engine.begin() as connection:
        connection.execute(text(
            """
            CREATE TABLE notifications_next (
                id INTEGER PRIMARY KEY,
                recipient_id INTEGER NOT NULL,
                kind VARCHAR(32) NOT NULL,
                title VARCHAR(200) NOT NULL,
                summary VARCHAR(255) NOT NULL,
                body TEXT NOT NULL,
                href VARCHAR(255) NOT NULL,
                alert_id INTEGER,
                complaint_id INTEGER,
                follow_up_id INTEGER,
                response_id INTEGER,
                read_at DATETIME,
                cleared_at DATETIME,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(recipient_id) REFERENCES users (id),
                FOREIGN KEY(alert_id) REFERENCES alerts (id),
                FOREIGN KEY(complaint_id) REFERENCES complaints (id),
                FOREIGN KEY(follow_up_id) REFERENCES follow_up_actions (id),
                FOREIGN KEY(response_id) REFERENCES complaint_responses (id)
            )
            """
        ))
        if "alert_id" in columns:
            cleared = "n.cleared_at" if "cleared_at" in columns else "NULL"
            connection.execute(text(
                f"""
                INSERT INTO notifications_next (
                    id, recipient_id, kind, title, summary, body, href,
                    alert_id, read_at, cleared_at, created_at
                )
                SELECT
                    n.id,
                    n.recipient_id,
                    'alert',
                    u.name,
                    a.dimension || ' · ' || printf('%.2f', a.score) || ' · ' || a.classification,
                    a.explanation,
                    '/manager/alerts/' || a.id,
                    n.alert_id,
                    n.read_at,
                    {cleared},
                    n.created_at
                FROM notifications AS n
                JOIN alerts AS a ON a.id = n.alert_id
                JOIN users AS u ON u.id = a.employee_id
                """
            ))
        connection.execute(text("DROP TABLE notifications"))
        connection.execute(text("ALTER TABLE notifications_next RENAME TO notifications"))
        connection.execute(text("CREATE INDEX ix_notifications_recipient_id ON notifications (recipient_id)"))
        connection.execute(text("CREATE INDEX ix_notifications_alert_id ON notifications (alert_id)"))


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth.routes import auth_bp
    from app.employee.routes import employee_bp
    from app.hr.routes import hr_bp
    from app.manager.routes import manager_bp
    from app.notifications.routes import notifications_bp
    from app.senior_manager.routes import senior_manager_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(hr_bp, url_prefix="/hr")
    app.register_blueprint(notifications_bp)
    app.register_blueprint(senior_manager_bp, url_prefix="/senior-manager")

    @app.template_filter("score")
    def score_filter(value):
        if value is None:
            return "—"
        return f"{value:.2f}"

    @app.template_filter("shortdate")
    def shortdate(value):
        if not value:
            return "—"
        return value.strftime("%d %b %Y")

    @app.template_filter("initials")
    def initials_filter(value):
        return initials(value)

    @app.context_processor
    def inject_notifications():
        if not current_user.is_authenticated:
            return {"notifications": [], "unread_notifications": 0}
        from app.services.notifications import notifications_for, unread_count

        notes = notifications_for(current_user)
        return {"notifications": notes, "unread_notifications": unread_count(notes)}

    @app.context_processor
    def inject_labels():
        return {
            "role_labels": ROLE_LABELS,
            "recipient_labels": RECIPIENT_LABELS,
            "classification_key": classification_key,
            "status_key": status_key,
            "classifications": CLASSIFICATIONS,
            "alert_classifications": CLASSIFICATIONS + (SIGNIFICANT,),
            "dimension_choices": DIMENSION_CHOICES,
            "alert_statuses": ALERT_STATUSES,
            "complaint_statuses": COMPLAINT_STATUSES,
        }

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def missing(_error):
        if current_user.is_authenticated:
            return render_template("errors/404.html"), 404
        return render_template(
            "errors/public_error.html",
            title="Page not found",
            message="That page does not exist.",
        ), 404

    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()
        _add_notification_cleared_column()
        _migrate_notifications()
        from app.services.notifications import backfill_event_notifications

        backfill_event_notifications()

    return app
