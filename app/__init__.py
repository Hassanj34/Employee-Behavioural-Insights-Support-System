from flask import Flask, render_template
from flask_login import current_user

from app.extensions import csrf, db, login_manager
from app.labels import RECIPIENT_LABELS, ROLE_LABELS, initials, status_key
from app.query_filters import ALERT_STATUSES, CLASSIFICATIONS, COMPLAINT_STATUSES, DIMENSION_CHOICES
from app.services.assessment_engine import SIGNIFICANT, classification_key
from config import Config


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
    from app.senior_manager.routes import senior_manager_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(hr_bp, url_prefix="/hr")
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

    return app
