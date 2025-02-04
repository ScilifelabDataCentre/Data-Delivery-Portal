"Utility functions and classes useful within the DDS."

####################################################################################################
# IMPORTS ################################################################################ IMPORTS #
####################################################################################################

# Standard library
import datetime
import os
import re
import typing
import urllib.parse
import time
import smtplib
from dateutil.relativedelta import relativedelta
import gc

# Installed
import botocore
from contextlib import contextmanager
import flask
from dds_web.errors import (
    AccessDeniedError,
    VersionMismatchError,
    DDSArgumentError,
    NoSuchProjectError,
    MaintenanceOngoingException,
    S3InfoNotFoundError,
)
import flask_mail
import flask_login
import werkzeug
import sqlalchemy

# # imports related to scheduling
import marshmallow
import wtforms


# Own modules
from dds_web.database import models
from dds_web import auth, mail
from dds_web.version import __version__

####################################################################################################
# VALIDATORS ########################################################################## VALIDATORS #
####################################################################################################

# General ################################################################################ General #


# Cannot have type hint for return due to models.Project giving circular import
def collect_project(project_id: str):
    """Get project object from database."""
    project = models.Project.query.filter(
        models.Project.public_id == sqlalchemy.func.binary(project_id)
    ).one_or_none()
    if not project:
        raise NoSuchProjectError(project=project_id)

    return project


def get_required_item(req: str, obj: werkzeug.datastructures.ImmutableMultiDict = None) -> str:
    """Get value from dict."""
    error_message = f"Missing required information: '{req}'"
    if not obj:
        raise DDSArgumentError(message=error_message)

    req_val = obj.get(req)
    if not req_val:
        raise DDSArgumentError(message=error_message)

    return req_val


# Cannot have type hint for return due to models.Project giving circular import
def verify_project_access(project) -> None:
    """Verify that current authenticated user has access to project."""
    if project not in auth.current_user().projects:
        raise AccessDeniedError(
            message="Project access denied.",
            username=auth.current_user().username,
            project=project.public_id,
        )


def verify_project_user_key(project) -> None:
    """Verify that current authenticated user has a row in projectUserKeys."""
    project_key = models.ProjectUserKeys.query.filter_by(
        project_id=project.id, user_id=auth.current_user().username
    ).one_or_none()
    if not project_key:
        msg = (
            "You have lost access to this project. "
            "This is likely due to a password reset, in which case you have lost access to all active projects. "
            f"In order to regain access to this project, please contact {project.responsible_unit.external_display_name} ({project.responsible_unit.contact_email}) and ask them to run 'dds project access fix'."
        )
        raise AccessDeniedError(
            message=msg,
            username=auth.current_user().username,
            project=project.public_id,
        )


def verify_cli_version(version_cli: str = None) -> None:
    """Verify that the CLI version in header is compatible with the web version."""
    # Verify that version is specified
    if not version_cli:
        raise VersionMismatchError(message="No version found in request, cannot proceed.")
    flask.current_app.logger.info(f"CLI VERSION: {version_cli}")

    # Split version string up into major, middle, minor
    version_cli_parts = version_cli.split(".")
    version_correct_parts = __version__.split(".")

    # The versions must have the same lengths
    if len(version_cli_parts) != len(version_correct_parts):
        raise VersionMismatchError(message="Incompatible version lengths.")

    # Verify that major versions match
    if version_cli_parts[0] != version_correct_parts[0]:
        raise VersionMismatchError


def contains_uppercase(indata):
    """Verify that string contains at least one upper case letter."""
    if not re.search("[A-Z]", indata):
        raise marshmallow.ValidationError("Required: at least one upper case letter.")


def contains_lowercase(indata):
    """Verify that string contains at least one lower case letter."""
    if not re.search("[a-z]", indata):
        raise marshmallow.ValidationError("Required: at least one lower case letter.")


def contains_digit_or_specialchar(indata):
    """Verify that string contains at least one special character OR digit."""
    if not any(re.search(x, indata) for x in ["[0-9]", "[#?!@$%^&*-]"]):
        raise marshmallow.ValidationError(
            "Required: at least one digit OR a special character (#?!@$%^&*-)."
        )


def contains_only_latin1(indata):
    """Verify that the password contains characters that can be encoded to latin-1.

    Non latin-1 chars cannot be passed to requests.
    """
    try:
        indata.encode("latin1")
    except UnicodeEncodeError as err:
        raise marshmallow.ValidationError("Contains invalid characters.")


def contains_disallowed_characters(indata):
    """Indatas like <f0><9f><98><80> cause issues in Project names etc."""
    disallowed = re.findall(r"[^(\w\s)]+", indata)
    if disallowed:
        disallowed = set(disallowed)  # unique values
        chars = "characters"
        raise marshmallow.ValidationError(
            f"The {chars if len(disallowed) > 1 else chars[:-1]} '{' '.join(disallowed)}' within '[italic]{indata}[/italic]' {'are' if len(disallowed) > 1 else 'is'} not allowed."
        )


def contains_unicode_emojis(indata):
    """Find unicode emojis in string - cause SQLAlchemyErrors."""
    # Ref: https://gist.github.com/Alex-Just/e86110836f3f93fe7932290526529cd1#gistcomment-3208085
    # Ref: https://en.wikipedia.org/wiki/Unicode_block
    EMOJI_PATTERN = re.compile(
        "(["
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "])"
    )
    emojis = re.findall(EMOJI_PATTERN, indata)
    if emojis:
        raise marshmallow.ValidationError(f"This input is not allowed: {''.join(emojis)}")


def email_not_taken(indata):
    """Validator - verify that email is not taken.

    If used by marshmallow Schema, this validator should never raise an error since the email
    field should not be changable and if it is the form validator should catch it.
    """
    if email_in_db(email=indata):
        raise marshmallow.validate.ValidationError("The email is already taken by another user.")


def email_taken(indata):
    """Validator - verify that email is taken."""
    if not email_in_db(email=indata):
        raise marshmallow.validate.ValidationError(
            "If the email is connected to a user within the DDS, you should receive an email with the password reset instructions."
        )


def username_not_taken(indata):
    """Validate that username is not taken.

    If used by marshmallow Schema, this validator should never raise an error since
    the form validator should catch it.
    """
    if username_in_db(username=indata):
        raise marshmallow.validate.ValidationError(
            "That username is taken. Please choose a different one."
        )


def valid_user_role(specified_role):
    """Returns whether or not a role is valid in the DDS."""
    return specified_role in [
        "Super Admin",
        "Unit Admin",
        "Unit Personnel",
        "Project Owner",
        "Researcher",
    ]


# wtforms ################################################################################ wtforms #


def username_contains_valid_characters():
    def _username_contains_valid_characters(form, field):
        """Validate that the username contains valid characters."""
        if not valid_chars_in_username(indata=field.data):
            raise wtforms.validators.ValidationError(
                "The username contains invalid characters. "
                "Usernames can only contain letters, digits and underscores (_)."
            )

    return _username_contains_valid_characters


def password_contains_valid_characters():
    def _password_contains_valid_characters(form, field):
        """Validate that the password contains valid characters and raise ValidationError."""
        errors = []
        validators = [
            contains_uppercase,
            contains_lowercase,
            contains_digit_or_specialchar,
            contains_only_latin1,
        ]
        for val in validators:
            try:
                val(indata=field.data)
            except marshmallow.ValidationError as valerr:
                errors.append(str(valerr).strip("."))

        if errors:
            raise wtforms.validators.ValidationError(", ".join(errors))

    return _password_contains_valid_characters


def username_not_taken_wtforms():
    def _username_not_taken(form, field):
        """Validate that the username is not taken already."""
        try:
            username_not_taken(indata=field.data)
        except marshmallow.validate.ValidationError as valerr:
            raise wtforms.validators.ValidationError(valerr)

    return _username_not_taken


def email_not_taken_wtforms():
    def _email_not_taken(form, field):
        """Validate that the email is not taken already."""
        try:
            email_not_taken(indata=field.data)
        except marshmallow.validate.ValidationError as valerr:
            raise wtforms.validators.ValidationError(valerr)

    return _email_not_taken


def email_taken_wtforms():
    def _email_taken(form, field):
        """Validate that the email exists."""
        try:
            email_taken(indata=field.data)
        except marshmallow.validate.ValidationError as valerr:
            raise wtforms.validators.ValidationError(valerr)

    return _email_taken


####################################################################################################
# FUNCTIONS ############################################################################ FUNCTIONS #
####################################################################################################


def verify_enough_unit_admins(unit_id: str, force_create: bool = False):
    """Verify that the unit has enough Unit Admins."""
    num_admins = models.UnitUser.query.filter_by(is_admin=True, unit_id=unit_id).count()
    if num_admins < 2:
        raise AccessDeniedError(
            message=(
                "Your unit does not have enough Unit Admins. "
                "At least two Unit Admins are required for a project to be created."
            )
        )

    if num_admins < 3 and not force_create:
        return (
            f"Your unit only has {num_admins} Unit Admins. This poses a high risk of data loss. "
            "We HIGHLY recommend that you do not create this project until there are more Unit "
            "Admins connected to your unit."
        )


def valid_chars_in_username(indata):
    """Check if the username contains only valid characters."""
    return bool(re.search(r"^[a-zA-Z0-9_\.-]+$", indata))


def email_in_db(email):
    """Check if the email is in the Email table."""
    if models.Email.query.filter_by(email=email).first():
        return True

    return False


def username_in_db(username):
    """Check if username is in the User table."""
    if models.User.query.filter_by(username=username).first():
        return True

    return False


def get_username_or_request_ip():
    """Util function for action logger: Try to identify the requester"""

    if auth.current_user():
        current_user = auth.current_user().username
    elif flask_login.current_user.is_authenticated:
        current_user = flask_login.current_user.username
    else:
        username = (
            flask.request.authorization.get("username") if flask.request.authorization else "---"
        )
        if flask.request.remote_addr:
            current_user = f"{username} ({flask.request.remote_addr})"  # log IP instead of username
        elif flask.request.access_route:
            current_user = (
                f"{username} ({flask.request.access_route[0]})"  # log IP instead of username
            )
        else:
            current_user = f"{username} (anonymous)"

    return current_user


def delrequest_exists(email):
    """Check if there is already a deletion request for that email."""
    if models.DeletionRequest.query.filter_by(email=email).first():
        return True
    return False


def send_reset_email(email_row, token):
    """Generate password reset email."""
    msg = flask_mail.Message(
        "WARNING! Password Reset Request for SciLifeLab Data Delivery System",
        recipients=[email_row.email],
    )

    # Need to attach the image to be able to use it
    msg.attach(
        "scilifelab_logo.png",
        "image/png",
        open(os.path.join(flask.current_app.static_folder, "img/scilifelab_logo.png"), "rb").read(),
        "inline",
        headers=[
            ["Content-ID", "<Logo>"],
        ],
    )

    link = flask.url_for("auth_blueprint.reset_password", token=token, _external=True)
    msg.body = flask.render_template("mail/password_reset.txt", link=link)
    msg.html = flask.render_template("mail/password_reset.html", link=link)

    mail.send(msg)


def send_project_access_reset_email(email_row, email, token):
    """Generate password reset email."""
    msg = flask_mail.Message(
        "WARNING! A Unit Admin has lost access",
        recipients=[email_row.email],
    )

    # Need to attach the image to be able to use it
    msg.attach(
        "scilifelab_logo.png",
        "image/png",
        open(os.path.join(flask.current_app.static_folder, "img/scilifelab_logo.png"), "rb").read(),
        "inline",
        headers=[
            ["Content-ID", "<Logo>"],
        ],
    )

    msg.body = flask.render_template("mail/project_access_reset.txt", email=email)
    msg.html = flask.render_template("mail/project_access_reset.html", email=email)

    mail.send(msg)


def is_safe_url(target):
    """Check if the url is safe for redirects."""
    ref_url = urllib.parse.urlparse(flask.request.host_url)
    test_url = urllib.parse.urlparse(urllib.parse.urljoin(flask.request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def current_time(to_midnight=False):
    """Return the current time for UTC"""

    curr_time = datetime.datetime.utcnow()
    if to_midnight:
        curr_time = curr_time.replace(hour=23, minute=59, second=59)

    return curr_time


def timestamp(dts=None, datetime_string=None, ts_format="%Y-%m-%d %H:%M:%S.%f"):
    """Gets the current time. Formats timestamp.

    Returns:
        str:    Timestamp in format 'YY-MM-DD_HH-MM-SS'

    """
    if datetime_string is not None:
        datetime_stamp = datetime.datetime.strptime(datetime_string, ts_format)
        return str(datetime_stamp.date())

    now = current_time() if dts is None else dts
    t_s = str(now.strftime(ts_format))
    return t_s


def rate_limit_from_config():
    return flask.current_app.config.get("TOKEN_ENDPOINT_ACCESS_LIMIT", "10/hour")


@contextmanager
def working_directory(path):
    """Contexter for changing working directory"""
    current_path = os.getcwd()
    try:
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        yield
    finally:
        os.chdir(current_path)


def page_query(q):
    offset = 0
    while True:
        r = False
        for elem in q.limit(1000).offset(offset):
            r = True
            yield elem
        offset += 1000
        if not r:
            break


def send_email_with_retry(msg, times_retried=0, obj=None):
    """Send email with retry on exception"""
    if obj is None:
        obj = mail
    try:
        obj.send(msg)
    except smtplib.SMTPException as err:
        # Wait a little bit
        time.sleep(10)
        # Retry twice
        if times_retried < 2:
            retry = times_retried + 1
            send_email_with_retry(msg, times_retried=retry, obj=obj)


def send_email_for_queue(msg):
    """TODO fix and maybe replace the main send_email function
    The other function cannot be used in a redis job because the
    connection object is not picklable.
    """
    try:
        mail.send(msg)
    except smtplib.SMTPException as err:
        # Wait a little bit
        time.sleep(10)
        # Retry twice, calls the other function TODO fix or replace
        send_email_with_retry(msg, times_retried=1, obj=mail)


def create_one_time_password_email(user, hotp_value):
    """Create HOTP email."""
    msg = flask_mail.Message(
        "DDS One-Time Authentication Code",
        recipients=[user.primary_email],
    )

    msg.attach(
        "scilifelab_logo.png",
        "image/png",
        open(os.path.join(flask.current_app.static_folder, "img/scilifelab_logo.png"), "rb").read(),
        "inline",
        headers=[
            ["Content-ID", "<Logo>"],
        ],
    )
    msg.body = flask.render_template(
        "mail/authenticate.txt", one_time_value=hotp_value.decode("utf-8")
    )
    msg.html = flask.render_template(
        "mail/authenticate.html", one_time_value=hotp_value.decode("utf-8")
    )

    return msg


def bucket_is_valid(bucket_name):
    """Verify that the bucket name is valid."""
    valid = False
    message = ""
    if not (3 <= len(bucket_name) <= 63):
        message = f"The bucket name has the incorrect length {len(bucket_name)}"
    elif re.findall(r"[^a-zA-Z0-9.-]", bucket_name):
        message = "The bucket name contains invalid characters."
    elif not bucket_name[0].isalnum():
        message = "The bucket name must begin with a letter or number."
    elif bucket_name.count(".") > 2:
        message = "The bucket name cannot contain more than two dots."
    elif bucket_name.startswith("xn--"):
        message = "The bucket name cannot begin with the 'xn--' prefix."
    elif bucket_name.endswith("-s3alias"):
        message = "The bucket name cannot end with the '-s3alias' suffix."
    else:
        valid = True
    return valid, message


def get_active_motds():
    """Return latest MOTD."""
    motds_active = (
        models.MOTD.query.filter_by(active=True).order_by(models.MOTD.date_created.desc()).all()
    )
    return motds_active or None


def calculate_bytehours(
    minuend: datetime.datetime, subtrahend: datetime.datetime, size_bytes: int
) -> float:
    """Calculate byte hours."""
    # Calculate the time difference as timedelta
    time_diff_timedelta = minuend - subtrahend

    # Convert the timedelta to hours
    hours_stored = time_diff_timedelta.total_seconds() / (60 * 60)

    # Calculate the bytehours
    bytehours = hours_stored * size_bytes

    return bytehours


def calculate_version_period_usage(version):
    bytehours: int = 0
    if not version.time_deleted and version.time_invoiced:
        # Existing and invoiced version
        now = current_time()
        bytehours = calculate_bytehours(
            minuend=now, subtrahend=version.time_invoiced, size_bytes=version.size_stored
        )
        version.time_invoiced = now
    elif version.time_deleted and not version.time_invoiced:
        # Version uploaded >and< deleted after last usage calculation
        bytehours = calculate_bytehours(
            minuend=version.time_deleted,
            subtrahend=version.time_uploaded,
            size_bytes=version.size_stored,
        )
        version.time_invoiced = version.time_deleted
    elif version.time_deleted != version.time_invoiced:
        # Version has been deleted after last usage calculation
        # (if version.time_deleted > version.time_invoiced)
        bytehours = calculate_bytehours(
            minuend=version.time_deleted,
            subtrahend=version.time_invoiced,
            size_bytes=version.size_stored,
        )
        version.time_invoiced = version.time_deleted
    elif not version.time_deleted and not version.time_invoiced:
        # New version: uploaded after last usage calculation
        now = current_time()
        bytehours = calculate_bytehours(
            minuend=now, subtrahend=version.time_uploaded, size_bytes=version.size_stored
        )
        version.time_invoiced = now

    return bytehours


def format_timestamp(
    timestamp_string: str = None, timestamp_object=None, timestamp_format: str = "%Y-%m-%d %H:%M:%S"
):
    """Change timestamp format."""
    if not timestamp_string and not timestamp_object:
        return

    if timestamp_string and timestamp_format != "%Y-%m-%d %H:%M:%S":
        raise ValueError(
            "Timestamp strings need to contain year, month, day, hour, minute and seconds."
        )

    if timestamp_object:
        timestamp_string = timestamp_object.strftime(timestamp_format)

    return datetime.datetime.strptime(timestamp_string, timestamp_format)


def bytehours_in_last_month(version):
    """Calculate number of terrabyte hours stored in last month."""
    # Current date and date a month ago
    now = format_timestamp(timestamp_object=current_time())
    a_month_ago = now - relativedelta(months=1)
    byte_hours: int = 0

    # 1. File uploaded after start (a month ago)
    if version.time_uploaded > a_month_ago:
        #   A. File not deleted --> now - uploaded
        if not version.time_deleted:
            byte_hours = calculate_bytehours(
                minuend=now,
                subtrahend=version.time_uploaded,
                size_bytes=version.size_stored,
            )

        #   B. File deleted --> deleted - uploaded
        else:
            byte_hours += calculate_bytehours(
                minuend=version.time_deleted,
                subtrahend=version.time_uploaded,
                size_bytes=version.size_stored,
            )

    # 2. File uploaded prior to start (a month ago)
    else:
        #   A. File not deleted --> now - thirty_days_ago
        if not version.time_deleted:
            byte_hours += calculate_bytehours(
                minuend=now, subtrahend=a_month_ago, size_bytes=version.size_stored
            )

        #   B. File deleted --> deleted - thirty_days_ago
        else:
            if version.time_deleted > a_month_ago:
                byte_hours += calculate_bytehours(
                    minuend=version.time_deleted,
                    subtrahend=a_month_ago,
                    size_bytes=version.size_stored,
                )

    return byte_hours


# maintenance check
def block_if_maintenance(user=None):
    """Block API requests if maintenance is ongoing and projects are busy."""
    # Get maintenance row
    maintenance: models.Maintenance = models.Maintenance.query.first()

    # Possibly block request if maintenance ongoing / planned
    if maintenance.active:
        if not user:
            # Endpoints accepting requests during active maintenance - only login for non-logged in users
            admin_endpoints: typing.List = [
                "/api/v1/user/encrypted_token",
                "/api/v1/user/second_factor",
            ]

            # Request not to accepted endpoint
            # OR request to accepted endpoint but project not specified or busy
            current_endpoint: str = flask.request.path
            if current_endpoint not in admin_endpoints:
                # Request not accepted during maintenance
                raise MaintenanceOngoingException()
        else:
            if user.role != "Super Admin":
                raise MaintenanceOngoingException()


def list_lost_files_in_project(project, s3_resource):
    """List lost files in project."""
    s3_filenames: set = set()
    db_filenames: set = set()

    # Check if bucket exists
    try:
        s3_resource.meta.client.head_bucket(Bucket=project.bucket)
    except botocore.exceptions.ClientError:
        missing_expected: bool = not project.is_active
        flask.current_app.logger.error(
            f"Project '{project.public_id}' bucket is missing. Expected: {missing_expected}"
        )
        raise

    # Get items in s3
    s3_filenames = set(entry.key for entry in s3_resource.Bucket(project.bucket).objects.all())

    # Get items in db
    try:
        db_filenames = set(entry.name_in_bucket for entry in project.files)
    except sqlalchemy.exc.OperationalError:
        flask.current_app.logger.critical("Unable to connect to db")
        raise

    # Differences
    diff_db = db_filenames.difference(s3_filenames)  # In db but not in S3
    diff_s3 = s3_filenames.difference(db_filenames)  # In S3 but not in db

    # List items
    if any([diff_db, diff_s3]):
        for file_entry in diff_db:
            flask.current_app.logger.info(
                "Entry %s (%s, %s) not found in S3 (but found in db)",
                file_entry,
                project.public_id,
                project.responsible_unit,
            )
        for file_entry in diff_s3:
            flask.current_app.logger.info(
                "Entry %s (%s, %s) not found in database (but found in s3)",
                file_entry,
                project.public_id,
                project.responsible_unit,
            )

    return diff_db, diff_s3


def use_sto4(unit_object, project_object) -> bool:
    """Check if project is newer than sto4 info, in that case return True."""
    project_id_logging: str = f"Safespring location for project '{project_object.public_id}': "
    sto4_endpoint_added = unit_object.sto4_start_time
    if sto4_endpoint_added and project_object.date_created > sto4_endpoint_added:
        if not all(
            [
                unit_object.sto4_endpoint,
                unit_object.sto4_name,
                unit_object.sto4_access,
                unit_object.sto4_secret,
            ]
        ):
            raise S3InfoNotFoundError(
                message=f"One or more sto4 variables are missing for unit {unit_object.public_id}."
            )
        flask.current_app.logger.info(f"{project_id_logging}sto4")
        return True

    flask.current_app.logger.info(f"{project_id_logging}sto2")
    return False


def add_uploaded_files_to_db(proj_in_db, log: typing.Dict):
    """Adds uploaded files to the database.

    Args:
        proj_in_db (dds_web.models.Project): The project to add the files to.
        log (typing.Dict): A dictionary containing information about the uploaded files.

    Returns:
        A tuple containing a list of files that were successfully added to the database,
        and a dictionary containing any errors that occurred while
        adding the files.
    """
    # Import necessary modules and initialize variables
    from dds_web import db
    from dds_web.api.api_s3_connector import ApiS3Connector

    errors = {}
    files_added = []

    flask.current_app.logger.info(type(log))
    # Loop through each file in the log
    for file, vals in log.items():
        status = vals.get("status")
        overwrite = vals.get("overwrite", False)

        # Check if the file was successfully uploaded but database not updated
        if not status or not status.get("failed_op") == "add_file_db":
            errors[file] = {"error": "Incorrect 'failed_op'."}
            continue

        # Connect to S3 and check if the file exists
        with ApiS3Connector(project=proj_in_db) as s3conn:
            try:
                _ = s3conn.resource.meta.client.head_object(
                    Bucket=s3conn.project.bucket, Key=vals["path_remote"]
                )
            except botocore.client.ClientError as err:
                if err.response["Error"]["Code"] == "404":
                    errors[file] = {"error": "File not found in S3", "traceback": err.__traceback__}
            else:
                try:
                    # Check if the file already exists in the database
                    file_object = models.File.query.filter(
                        sqlalchemy.and_(
                            models.File.name == sqlalchemy.func.binary(file),
                            models.File.project_id == proj_in_db.id,
                        )
                    ).first()

                    # If the file already exists, create a new version of it if "--overwrite" was specified
                    if file_object:
                        if overwrite:
                            try:
                                new_file_version(existing_file=file_object, new_info=vals)
                                files_added.append(file_object)
                            except KeyError as err:
                                errors[file] = {"error": f"Missing key: {err}"}
                        else:
                            errors[file] = {"error": "File already in database."}

                    # If the file does not exist, create a new file and version
                    else:
                        new_file = models.File(
                            name=file,
                            name_in_bucket=vals["path_remote"],
                            subpath=vals["subpath"],
                            project_id=proj_in_db.id,
                            size_original=vals["size_raw"],
                            size_stored=vals["size_processed"],
                            compressed=not vals["compressed"],
                            public_key=vals["public_key"],
                            salt=vals["salt"],
                            checksum=vals["checksum"],
                        )
                        new_version = models.Version(
                            size_stored=new_file.size_stored,
                            time_uploaded=datetime.datetime.utcnow(),
                        )
                        proj_in_db.file_versions.append(new_version)
                        proj_in_db.files.append(new_file)
                        new_file.versions.append(new_version)

                        db.session.add(new_file)
                        db.session.commit()
                        files_added.append(new_file)
                except (
                    sqlalchemy.exc.IntegrityError,
                    sqlalchemy.exc.OperationalError,
                    sqlalchemy.exc.SQLAlchemyError,
                ) as err:
                    errors[file] = {"error": str(err)}
                    db.session.rollback()
    if errors:
        flask.current_app.logger.error(f"Error in new_file_version: {errors}")

    return files_added, errors


def new_file_version(existing_file, new_info):
    """
    Create new version of a file.

    Args:
        existing_file (dds_web.models.File): The existing file to create a new version of.
        new_info (dict): A dictionary containing information about the new version of the file.

    Returns:
        None
    """
    from dds_web import db
    import dds_web.utils

    # Get project
    project = existing_file.project

    # Get versions
    current_file_version = models.Version.query.filter(
        sqlalchemy.and_(
            models.Version.active_file == sqlalchemy.func.binary(existing_file.id),
            models.Version.time_deleted.is_(None),
        )
    ).all()

    # If there is more than one version of the file which does not yet have a deletion timestamp, log a warning
    if len(current_file_version) > 1:
        flask.current_app.logger.warning(
            "There is more than one version of the file "
            "which does not yet have a deletion timestamp."
        )

    # Same timestamp for deleted and created new version
    new_timestamp = dds_web.utils.current_time()

    # Set the deletion timestamp for the latests version of the file
    for version in current_file_version:
        if version.time_deleted is None:
            version.time_deleted = new_timestamp

    # Update file info
    existing_file.subpath = new_info["subpath"]
    existing_file.size_original = new_info["size_raw"]
    existing_file.size_stored = new_info["size_processed"]
    existing_file.compressed = not new_info["compressed"]
    existing_file.salt = new_info["salt"]
    existing_file.public_key = new_info["public_key"]
    existing_file.time_uploaded = new_timestamp
    existing_file.checksum = new_info["checksum"]

    # Create a new version of the file
    new_version = models.Version(
        size_stored=new_info["size_processed"],
        time_uploaded=new_timestamp,
        active_file=existing_file.id,
        project_id=project,
    )

    # Update foreign keys and relationships
    project.file_versions.append(new_version)
    existing_file.versions.append(new_version)

    # Add the new version to the database and commit the changes
    db.session.add(new_version)
    db.session.commit()

    # Clean up information
    del new_info
