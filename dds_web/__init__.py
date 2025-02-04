"""Initialize Flask app."""

####################################################################################################
# IMPORTS ################################################################################ IMPORTS #
####################################################################################################

# Standard library
import logging
import pathlib
import sys
import os

# Installed
import flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from logging.config import dictConfig
from authlib.integrations import flask_client as auth_flask_client
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
import flask_mail
import flask_login
import flask_migrate
import rq_dashboard

# import flask_qrcode
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlalchemy
import structlog
import werkzeug

####################################################################################################
# GLOBAL VARIABLES ############################################################## GLOBAL VARIABLES #
####################################################################################################

# Database - not yet init
db = SQLAlchemy()

# Email setup - not yet init
mail = flask_mail.Mail()

# Marshmallows for parsing and validating
ma = Marshmallow()

# Authentication
oauth = auth_flask_client.OAuth()
basic_auth = HTTPBasicAuth()
auth = HTTPTokenAuth()

# Login - web routes
login_manager = flask_login.LoginManager()
login_manager.login_view = "auth_blueprint.login"
login_manager.session_protection = "strong"

# Actions for logging
actions = {}

# Limiter
limiter = Limiter(key_func=get_remote_address)

# Migration
migrate = flask_migrate.Migrate()


####################################################################################################
# FUNCTIONS ############################################################################ FUNCTIONS #
####################################################################################################


class FilterMaintenanceExc(logging.Filter):

    def filter(record):
        """
        Filters log records to exclude those with MaintenanceOngoingException.
        Returns:
            bool: True if the log record should be logged, False if it should be filtered out.
        """
        from dds_web.errors import MaintenanceOngoingException

        # Check if the log record does not have an exception or if the exception is not MaintenanceOngoingException
        return record.exc_info is None or record.exc_info[0] != MaintenanceOngoingException


def setup_logging(app):
    """Setup loggers"""

    def action_wrapper(_, __, event_dict):
        return {"action": event_dict}

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(message)s"},
                "general": {"format": "[%(asctime)s] %(module)s [%(levelname)s] %(message)s"},
            },
            "handlers": {
                "general": {
                    "level": logging.DEBUG,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": pathlib.Path(app.config.get("LOGS_DIR")) / pathlib.Path("dds.log"),
                    "formatter": "general",
                    "maxBytes": app.config.get("LOG_MAX_SIZE"),
                    "backupCount": app.config.get("LOG_BACKUP_COUNT"),
                },
                "actions": {
                    "level": logging.INFO,
                    "class": "logging.handlers.RotatingFileHandler",
                    "maxBytes": app.config.get("LOG_MAX_SIZE"),
                    "backupCount": app.config.get("LOG_BACKUP_COUNT"),
                    "filename": pathlib.Path(app.config.get("LOGS_DIR"))
                    / pathlib.Path("actions.log"),
                    "formatter": "default",
                },
                "console": {
                    "level": logging.DEBUG,
                    "class": "logging.StreamHandler",
                    "formatter": "general",
                },
            },
            "loggers": {
                "general": {
                    "handlers": ["general", "console"],
                    "level": logging.DEBUG,
                    "propagate": False,
                },
                "actions": {
                    "handlers": ["actions"],
                    "level": logging.INFO,
                    "propagate": False,
                },
            },
        }
    )

    structlog.configure(
        processors=[
            # Merge the bindings from Thread-Local Context, a sort of global context storage.
            structlog.threadlocal.merge_threadlocal,
            # Mimics the level configuration of the standard logging lib.
            # e.g. logger.debug() event will be dropped if logging level is set to INFO or higher.
            structlog.stdlib.filter_by_level,
            # Add the name of the logger to event dict.
            structlog.stdlib.add_logger_name,
            # Add log level to event dict.
            structlog.stdlib.add_log_level,
            # Perform %-style formatting.
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add a timestamp to the event dict in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            # If the "stack_info" key in the event dict is true, remove it and
            # render the current stack trace in the "stack" key.
            structlog.processors.StackInfoRenderer(),
            # If the "exc_info" key in the event dict is either true or a
            # sys.exc_info() tuple, remove "exc_info" and render the exception
            # with traceback into the "exception" key.
            structlog.processors.format_exc_info,
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            # Wrap each log row under the parent key "action": {"action": <json dict rendered below>}
            # Why: To enable filtering of the action logs
            action_wrapper,
            # Render the final event dict as JSON.
            structlog.processors.JSONRenderer(),
        ],
        # `wrapper_class` is the bound logger that you get back from
        # get_logger(). This one imitates `logging.Logger`.
        wrapper_class=structlog.stdlib.BoundLogger,
        # `logger_factory` is used to create wrapped loggers that are used for
        # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
        # string) from the final processor (`JSONRenderer`) will be passed to
        # the method of the same name as that you've called on the bound logger.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Effectively freeze configuration after creating the first bound
        # logger.
        cache_logger_on_first_use=True,
    )

    # Add custom filter to the logger
    logging.getLogger("general").addFilter(FilterMaintenanceExc)


def create_app(testing=False, database_uri=None):
    try:
        """Construct the core application."""
        # Initiate app object
        app = flask.Flask(__name__, instance_relative_config=False)

        # All variables in the env that start with FLASK_* will be loaded into the app config
        # 'FLASK_' will be dropped, e.g. FLASK_TESTVAR will be loaded as TESTVAR
        app.config.from_prefixed_env()

        # Default development config
        app.config.from_object("dds_web.config.Config")

        # User config file, if e.g. using in production
        app.config.from_envvar("DDS_APP_CONFIG", silent=True)

        # redis dashboard
        app.config.from_object(rq_dashboard.default_settings)
        rq_dashboard.web.setup_rq_connection(app)

        # Test related configs
        if database_uri is not None:
            app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
        # Disables error catching during request handling
        app.config["TESTING"] = testing
        if testing:
            # Simplifies testing as we don't test the session protection anyway
            login_manager.session_protection = "basic"

        @app.before_request
        def prepare():
            """Populate flask globals for template rendering"""
            from dds_web.utils import verify_cli_version, get_active_motds, block_if_maintenance

            # Verify cli version compatible
            if "api/v1" in flask.request.path:
                verify_cli_version(version_cli=flask.request.headers.get("X-Cli-Version"))
            elif "api/v3" in flask.request.path:  # experimental v3 version
                # If version api is not provided, it gets the data from the __version__ file
                # When v3 is finallized, this should be removed and the __version__ file should be updated
                pass

            # Get message of the day
            flask.g.motd = get_active_motds()

            flask.g.current_user = None
            flask.g.current_user_emails = None
            if auth.current_user():
                flask.g.current_user = auth.current_user().username
                flask.g.current_user_emails = auth.current_user().emails
            elif flask_login.current_user.is_authenticated:
                flask.g.current_user = flask_login.current_user.username
                flask.g.current_user_emails = flask_login.current_user.emails
            elif flask.request.authorization:
                flask.g.current_user = flask.request.authorization.get("username")
                flask.g.current_user_emails = flask.request.authorization.get("emails")

        # Setup logging handlers
        setup_logging(app)

        # Adding limiter logging
        for handler in app.logger.handlers:
            limiter.logger.addHandler(handler)

        # Set app.logger as the general logger
        app.logger = logging.getLogger("general")
        app.logger.info("Logging initiated.")

        # Initialize database
        db.init_app(app)

        # Initialize mail setup
        mail.init_app(app)

        # Avoid very extensive logging when sending emails
        app.extensions["mail"].debug = 0

        # Initialize marshmallows
        ma.init_app(app)

        # Errors, TODO: Move somewhere else?
        @app.errorhandler(sqlalchemy.exc.SQLAlchemyError)
        def handle_sqlalchemyerror(e):
            return f"SQLAlchemyError: {e}", 500  # TODO: Fix logging and a page

        # Initialize login manager
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(user_id)

        if app.config["REVERSE_PROXY"]:
            app.wsgi_app = ProxyFix(app.wsgi_app)

        # Initialize limiter
        limiter._storage_uri = app.config.get("RATELIMIT_STORAGE_URL")
        limiter.init_app(app)

        # Initialize migrations
        migrate.init_app(app, db)

        # initialize OIDC
        oauth.init_app(app)
        oauth.register(
            "default_login",
            client_secret=app.config.get("OIDC_CLIENT_SECRET"),
            client_id=app.config.get("OIDC_CLIENT_ID"),
            server_metadata_url=app.config.get("OIDC_ACCESS_TOKEN_URL"),
            client_kwargs={"scope": "openid profile email"},
        )

        # Import flask commands - all
        from dds_web.commands import (
            fill_db_wrapper,
            create_new_unit,
            update_uploaded_file_with_log,
            lost_files_s3_db,
            set_available_to_expired,
            set_expired_to_archived,
            delete_invites,
            monthly_usage,
            send_usage,
            collect_stats,
            monitor_usage,
            update_unit_sto4,
            update_unit_quota,
            run_worker,
        )

        # Add flask commands - general
        app.cli.add_command(fill_db_wrapper)
        app.cli.add_command(create_new_unit)
        app.cli.add_command(update_unit_sto4)
        app.cli.add_command(update_unit_quota)
        app.cli.add_command(update_uploaded_file_with_log)
        app.cli.add_command(lost_files_s3_db)

        # Add flask commands - cronjobs
        app.cli.add_command(set_available_to_expired)
        app.cli.add_command(set_expired_to_archived)
        app.cli.add_command(delete_invites)
        app.cli.add_command(monthly_usage)
        app.cli.add_command(send_usage)
        app.cli.add_command(collect_stats)
        app.cli.add_command(monitor_usage)
        app.cli.add_command(run_worker)

        # Make version available inside jinja templates:
        @app.template_filter("dds_version")
        def dds_version_filter(_):
            return os.environ.get("DDS_VERSION", "Unknown")

        with app.app_context():  # Everything in here has access to sessions
            from dds_web.database import models

            # Need to import auth so that the modifications to the auth objects take place
            import dds_web.security.auth

            # Register blueprints
            from dds_web.api import api_blueprint, api_blueprint_v3
            from dds_web.web.root import pages
            from dds_web.web.user import auth_blueprint
            from flask_swagger_ui import get_swaggerui_blueprint

            # base url for the api documentation
            SWAGGER_URL_1 = "/api/documentation/v1"
            SWAGGER_URL_3 = "/api/documentation/v3"

            # path where the swagger file(s) are localted in the repository
            API_URL_V1 = "/static/swagger.yaml"
            API_URL_V3 = "/static/swaggerv3.yaml"

            # register blueprint(s) for the documentation
            swagger_ui_blueprint_v1 = get_swaggerui_blueprint(
                SWAGGER_URL_1,
                API_URL_V1,
                config={
                    "app_name": "DDS API Documentation",
                    "defaultModelsExpandDepth": -1,
                    "layout": "BaseLayout",
                },
            )
            swagger_ui_blueprint_v3 = get_swaggerui_blueprint(
                SWAGGER_URL_3,
                API_URL_V3,
                config={
                    "app_name": "DDS API Documentation",
                    "defaultModelsExpandDepth": -1,
                    "layout": "BaseLayout",
                },
            )

            # two documentation and api versions, v3 will contain the new endpoints fixed
            app.register_blueprint(swagger_ui_blueprint_v1, url_prefix=SWAGGER_URL_1, name="v1")
            app.register_blueprint(swagger_ui_blueprint_v3, url_prefix=SWAGGER_URL_3, name="v3")
            app.register_blueprint(api_blueprint, url_prefix="/api/v1")
            app.register_blueprint(api_blueprint_v3, url_prefix="/api/v3")

            app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
            app.register_blueprint(pages, url_prefix="")
            app.register_blueprint(auth_blueprint, url_prefix="")

            ENCRYPTION_KEY_BIT_LENGTH = 256
            ENCRYPTION_KEY_CHAR_LENGTH = int(ENCRYPTION_KEY_BIT_LENGTH / 8)

            if len(app.config.get("SECRET_KEY")) != ENCRYPTION_KEY_CHAR_LENGTH:
                from dds_web.errors import KeyLengthError

                raise KeyLengthError(ENCRYPTION_KEY_CHAR_LENGTH)

            return app
    except sqlalchemy.exc.OperationalError as err:
        app.logger.exception("The database seems to be down.")
        sys.exit(1)
