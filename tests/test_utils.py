import marshmallow
from dds_web import utils
import pytest
from unittest.mock import patch, MagicMock
from unittest.mock import PropertyMock

from dds_web import db
from dds_web.database import models
from dds_web.errors import (
    AccessDeniedError,
    DDSArgumentError,
    NoSuchProjectError,
    VersionMismatchError,
)
import flask
import flask_login
import datetime
from pyfakefs.fake_filesystem import FakeFilesystem
import os
import flask_mail
from flask.testing import FlaskClient
import requests_mock
import werkzeug
from dateutil.relativedelta import relativedelta
import boto3
import botocore
import sqlalchemy
from _pytest.logging import LogCaptureFixture

# Variables

url: str = "http://localhost"

# Mocking


def mock_nosuchbucket(*_, **__):
    raise botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "NoSuchBucket"}}, operation_name="Test"
    )


def mock_items_in_bucket():
    class Object(object):
        pass

    list_of_items = []
    for i in range(20):
        obj = Object()
        obj.key = f"testing{i}"
        list_of_items.append(obj)

    return list_of_items


# collect_project


def test_collect_project_project_doesnt_exist(client: flask.testing.FlaskClient) -> None:
    """Non existent project should give error."""
    with pytest.raises(NoSuchProjectError) as err:
        utils.collect_project(project_id="nonexistent")
    assert "The specified project does not exist." in str(err.value)


def test_collect_project_ok(client: flask.testing.FlaskClient):
    """Existing project should return project object."""
    # Get project from database to make sure it exists
    existing_project = models.Project.query.first()

    # Should return project
    project = utils.collect_project(project_id=existing_project.public_id)
    assert project and project == existing_project


# get_required_item


def test_get_required_item_no_obj(client: flask.testing.FlaskClient) -> None:
    """Get item from dict, but no dict specified."""
    with pytest.raises(DDSArgumentError) as err:
        utils.get_required_item(req="project")
    assert "Missing required information: 'project'" in str(err.value)


def test_get_required_item_not_in_obj(client: flask.testing.FlaskClient) -> None:
    """If the required item is not in the dict, there should be an error."""
    with pytest.raises(DDSArgumentError) as err:
        utils.get_required_item(obj={"test": "something"}, req="project")
    assert "Missing required information: 'project'" in str(err.value)


def test_get_required_item_ok(client: flask.testing.FlaskClient) -> None:
    """If dict contains item, value should be returned."""
    value = utils.get_required_item(obj={"project": "project_id"}, req="project")
    assert value == "project_id"


def test_verify_project_access_denied(client: flask.testing.FlaskClient) -> None:
    """A project must have access to the project, otherwise error."""
    # First user
    user1 = models.UnitUser.query.filter_by(unit_id=1).first()
    assert user1

    # Second user
    user2 = models.UnitUser.query.filter_by(unit_id=2).first()
    assert user2

    # Get project for unit 2
    project = models.Project.query.filter_by(unit_id=2).first()
    assert project

    # Set auth.current_user
    flask.g.flask_httpauth_user = user1

    # Verify project access -- not ok
    with pytest.raises(AccessDeniedError) as err:
        utils.verify_project_access(project=project)
    assert "Project access denied" in str(err.value)


def test_verify_project_access_ok(client: flask.testing.FlaskClient) -> None:
    """A project must have access to the project, otherwise error."""
    # First user
    user1 = models.UnitUser.query.filter_by(unit_id=1).first()
    assert user1

    # Get project for unit 1
    project = models.Project.query.filter_by(unit_id=1).first()
    assert project

    # Set auth.current_user
    flask.g.flask_httpauth_user = user1

    # Verify project access -- not ok
    utils.verify_project_access(project=project)


def test_verify_project_user_key_denied(client: flask.testing.FlaskClient) -> None:
    """A user must have an entry in projectUserKeys to access a project."""
    # User
    user = models.UnitUser.query.filter_by(unit_id=1).first()
    assert user

    # Get project
    project = models.Project.query.filter_by(unit_id=1).first()
    assert project

    # get projectUserKey
    projectUserKey = models.ProjectUserKeys.query.filter_by(
        project_id=project.id, user_id=user.username
    ).one_or_none()
    assert projectUserKey

    # delete projectUserKey
    db.session.delete(projectUserKey)
    db.session.commit()

    # verify no projectUserKey
    projectUserKey = models.ProjectUserKeys.query.filter_by(
        project_id=project.id, user_id=user.username
    ).one_or_none()
    assert not projectUserKey

    # Set auth.current_user
    flask.g.flask_httpauth_user = user

    # Verify project access -- not ok
    with pytest.raises(AccessDeniedError) as err:
        utils.verify_project_user_key(project=project)

    error_msg = (
        "You have lost access to this project. "
        "This is likely due to a password reset, in which case you have lost access to all active projects. "
        f"In order to regain access to this project, please contact {project.responsible_unit.external_display_name} ({project.responsible_unit.contact_email}) and ask them to run 'dds project access fix'."
    )
    assert error_msg in str(err.value)


def test_verify_project_user_key_ok(client: flask.testing.FlaskClient) -> None:
    """A user must have an entry in projectUserKeys to access a project."""
    # user
    user = models.UnitUser.query.filter_by(unit_id=1).first()
    assert user

    # Get project
    project = models.Project.query.filter_by(unit_id=1).first()
    assert project

    # get projectUserKey
    projectUserKey = models.ProjectUserKeys.query.filter_by(
        project_id=project.id, user_id=user.username
    ).one_or_none()
    assert projectUserKey

    # Set auth.current_user
    flask.g.flask_httpauth_user = user

    # Verify project access -- ok
    utils.verify_project_access(project=project)


# verify_cli_version


def test_verify_cli_version_no_version_in_request(client: flask.testing.FlaskClient) -> None:
    """Version is required in order to compare."""
    with pytest.raises(VersionMismatchError) as err:
        utils.verify_cli_version()
    assert "No version found in request, cannot proceed." in str(err.value)


def test_verify_cli_version_incompatible(client: flask.testing.FlaskClient) -> None:
    """Incompatible versions should return an error."""
    with pytest.raises(VersionMismatchError) as err:
        utils.verify_cli_version(version_cli="0.0.0")
    assert "You're using an old CLI version, please upgrade to the latest one." in str(err.value)


def test_verify_cli_version_incorrect_length(client: flask.testing.FlaskClient) -> None:
    """Incorrect version lengths should return an error."""
    with pytest.raises(VersionMismatchError) as err:
        utils.verify_cli_version(version_cli="0.0.0.0")
    assert "Incompatible version lengths." in str(err.value)


def test_verify_cli_version_ok(client: flask.testing.FlaskClient) -> None:
    """Compatible versions should not fail."""
    from dds_web import version

    utils.verify_cli_version(version_cli=version.__version__)


# contains_uppercase


def test_contains_uppercase_false():
    """Test if a lower case string contains an upper case character."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_uppercase(indata="nouppercasehere")
    assert "Required: at least one upper case letter." in str(err.value)


def test_contains_uppercase_true():
    """Test if a string contains an upper case letter."""
    utils.contains_uppercase(indata="ThereisanuppercaseInhere")


# contains_lowercase


def test_contains_lowercase_false():
    """Test if a upper case string contains a lower case character."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_lowercase(indata="NOLOWERCASEHERE")
    assert "Required: at least one lower case letter." in str(err.value)


def test_contains_lowercase_true():
    """Test if a string contains a lower case character."""
    utils.contains_lowercase(indata="ThereISALOWERCASE")


# contains_digit_or_specialchar


def test_contains_digit_or_specialchar_no_digit_or_char():
    """Test if a string without a digit or char contains a digit and char."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_digit_or_specialchar(indata="Thereisnodigitorchar")
    assert "Required: at least one digit OR a special character (#?!@$%^&*-)." in str(err.value)


def test_contains_digit_or_specialchar_no_digit():
    """Test if a string without a digit contains a digit."""
    utils.contains_digit_or_specialchar(indata="Thereisnodigitbutthereisacharhere$")


def test_contains_digit_or_specialchar_no_char():
    """Test if a string without a char contains a char."""
    utils.contains_digit_or_specialchar(indata="Thereisnodigitorchar1")


# contains_only_latin1


def test_contains_only_latin1_invalid():
    """Non latin 1 encodable characters should raise a validation error with specific message."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_only_latin1(indata="testing€")
    assert "Contains invalid characters." in str(err.value)


def test_contains_only_latin1_ok():
    """Only latin 1 encodable characters should be allowed and give no exceptions."""
    returned = utils.contains_only_latin1(indata="testing")
    assert returned is None


# contains_disallowed_characters


def test_contains_disallowed_characters_contains_char():
    """Test if a string contains any disallowed characters."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_disallowed_characters(indata="Also contains <")
    assert "The character '<' within" in str(err.value)
    assert "is not allowed" in str(err.value)


def test_contains_disallowed_characters_contains_multiple_char():
    """Test if a string contains any disallowed characters - multiple."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_disallowed_characters(indata="Also contains < $")
    assert "The characters '$ <' within" in str(err.value) or "The characters '< $' within" in str(
        err.value
    )
    assert "are not allowed" in str(err.value)


def test_contains_disallowed_characters():
    """Test if a string contains any disallowed characters - it doesn't."""
    utils.contains_disallowed_characters(indata="Does not contain any disallowed character")


# contains_unicode_emojis


def test_contains_unicode_emojis_true():
    """Test if a string contains any unicode emojis."""
    # Contains flag
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F1E0")
    assert "This input is not allowed: \U0001F1E0" in str(err.value)

    # Contains symbol
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F300\U0001F301")
    assert "This input is not allowed: \U0001F300\U0001F301" in str(err.value)

    # Contains emoticons
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F600\U0001F601")
    assert "This input is not allowed: \U0001F600\U0001F601" in str(err.value)

    # Contains transport
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F680\U0001F681")
    assert "This input is not allowed: \U0001F680\U0001F681" in str(err.value)

    # Contains alchemical symbols
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F700\U0001F701")
    assert "This input is not allowed: \U0001F700\U0001F701" in str(err.value)

    # Contains geometric shapes extended
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F780\U0001F781")
    assert "This input is not allowed: \U0001F780\U0001F781" in str(err.value)

    # Contains supplemental arrows-c
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F800\U0001F801")
    assert "This input is not allowed: \U0001F800\U0001F801" in str(err.value)

    # Contains supplemental symbols and pictographs
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001F900\U0001F901")
    assert "This input is not allowed: \U0001F900\U0001F901" in str(err.value)

    # Contains chess symbols
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001FA00\U0001FA01")
    assert "This input is not allowed: \U0001FA00\U0001FA01" in str(err.value)

    # Contains symbols and pictographs
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U0001FA70\U0001FA71")
    assert "This input is not allowed: \U0001FA70\U0001FA71" in str(err.value)

    # Contains dingbats
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.contains_unicode_emojis(indata="\U00002702\U00002703")
    assert "This input is not allowed: \U00002702\U00002703" in str(err.value)


def test_contains_unicode_emojis_false():
    """Test if a string contains any unicode emojis."""
    utils.contains_unicode_emojis(indata="Doesn't contain any emojis.")


# email_not_taken


def test_email_not_taken_true(client):
    """Check if a non taken email is taken or not."""
    utils.email_not_taken(indata="nonexistentemail@mail.com")


def test_email_not_taken_false(client):
    """Check if a taken email is taken or not."""
    from dds_web import db
    from dds_web.database import models

    user = db.session.query(models.User).first()
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.email_not_taken(indata=user.primary_email)
    assert "The email is already taken by another user." in str(err.value)


# email_taken


def test_email_taken_false(client):
    """Check if a non taken email is taken or not."""
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.email_taken(indata="nonexistentemail@mail.com")
    assert "If the email is connected to a user within the DDS" in str(err.value)


def test_email_taken_false(client):
    """Check if a taken email is taken or not."""
    from dds_web import db
    from dds_web.database import models

    user = db.session.query(models.User).first()
    utils.email_taken(indata=user.primary_email)


# username_not_taken


def test_username_not_taken_taken(client):
    """Check that a username is taken."""
    from dds_web import db
    from dds_web.database import models

    user = db.session.query(models.User).first()
    with pytest.raises(marshmallow.ValidationError) as err:
        utils.username_not_taken(indata=user.username)
    assert "That username is taken. Please choose a different one." in str(err.value)


def test_username_not_taken_nottaken(client):
    """Check that a username is not taken."""
    utils.username_not_taken(indata="nosuchusername")


# valid_user_role


def test_valid_user_role_false():
    """Test if a role is incorrect."""
    valid = utils.valid_user_role(specified_role="Some Role")
    assert not valid


def test_valid_user_role_false():
    """Test if a role is incorrect."""
    valid = utils.valid_user_role(specified_role="Super Admin")
    assert valid

    valid = utils.valid_user_role(specified_role="Unit Admin")
    assert valid

    valid = utils.valid_user_role(specified_role="Unit Personnel")
    assert valid

    valid = utils.valid_user_role(specified_role="Project Owner")
    assert valid

    valid = utils.valid_user_role(specified_role="Researcher")
    assert valid


# username_contains_valid_characters

# class TestForm(flask_wtf.FlaskForm):
#     """User registration form."""
#     username = wtforms.StringField(
#         "Username",
#         validators=[
#             utils.username_contains_valid_characters(),
#         ],
#     )

# def test_username_contains_valid_characters(client):
#     """"""
#     form = TestForm()
#     form.username.data = "hehej?"
#     with pytest.raises(wtforms.validators.ValidationError) as err:
#         form.validate()

# verify_enough_unit_admins


def test_verify_enough_unit_admins_less_than_2(client):
    """Verify that an exception is thrown when a unit has less than 2 unit admins."""
    # Get unit
    unit = db.session.query(models.Unit).first()
    assert unit

    # Get number of admins
    num_admins = db.session.query(models.UnitUser).filter_by(is_admin=True, unit_id=unit.id).count()
    assert num_admins == 1

    # Run function
    with pytest.raises(AccessDeniedError) as err:
        utils.verify_enough_unit_admins(unit_id=unit.id)
    assert "Your unit does not have enough Unit Admins" in str(err.value)


def test_verify_enough_unit_admins_less_than_3(client):
    """Verify that an error message is returned when a unit has less than 3 unit admins."""
    # Unit ID
    unit_id = 1

    # Get unit
    unit = db.session.query(models.Unit).filter_by(id=unit_id).one_or_none()
    assert unit

    # Get number of admins
    num_admins = db.session.query(models.UnitUser).filter_by(is_admin=True, unit_id=unit_id).count()
    assert num_admins == 1

    # Create another unit admin
    from tests import test_project_creation

    test_project_creation.create_unit_admins(num_admins=1, unit_id=unit_id)

    # Get number of admins
    num_admins = db.session.query(models.UnitUser).filter_by(is_admin=True, unit_id=unit_id).count()
    assert num_admins == 2

    # Run function
    response = utils.verify_enough_unit_admins(unit_id=unit_id)
    assert "Your unit only has 2 Unit Admins. This poses a high risk of data loss" in response


def test_verify_enough_unit_admins_ok(client):
    """Verify that no exception is thrown and no error is returned if there are at least 3 unit admins."""
    # Unit ID
    unit_id = 1

    # Get unit
    unit = db.session.query(models.Unit).filter_by(id=unit_id).one_or_none()
    assert unit

    # Get number of admins
    num_admins = db.session.query(models.UnitUser).filter_by(is_admin=True, unit_id=unit_id).count()
    assert num_admins == 1

    # Create another unit admin
    from tests import test_project_creation

    test_project_creation.create_unit_admins(num_admins=2, unit_id=unit_id)

    # Get number of admins
    num_admins = db.session.query(models.UnitUser).filter_by(is_admin=True, unit_id=unit_id).count()
    assert num_admins == 3

    # Run function
    response = utils.verify_enough_unit_admins(unit_id=unit_id)
    assert not response


# valid_chars_in_username


def test_valid_chars_in_username_only_valid():
    """Verify return true if contains only valid characters."""
    response: bool = utils.valid_chars_in_username(indata="valid")
    assert response


def test_valid_chars_in_username_some_invalid():
    """Verify return false if contains only some invalid characters."""
    response: bool = utils.valid_chars_in_username(indata="invalid$")
    assert not response


# email_in_db


def test_email_in_db_true(client):
    """Verify return True if email is in database."""
    # Get email known to be in database
    email_row: models.Email = db.session.query(models.Email).first()
    assert email_row

    # Check that found in database
    response: bool = utils.email_in_db(email=email_row.email)
    assert response


def test_email_in_db_false(client):
    """Verify return False if email is not in database."""
    # Define email
    email_address: str = "notindb@mail.com"

    # Check that email is not in database
    email_row: models.Email = (
        db.session.query(models.Email).filter_by(email="notindb@mail.com").first()
    )
    assert not email_row

    # Check that found in database
    response: bool = utils.email_in_db(email=email_address)
    assert not response


# username_in_db


def test_username_in_db_true(client):
    """Verify return True if username is in database."""
    # Get username known to be in database
    user_in_db: models.User = db.session.query(models.User).first()
    assert user_in_db

    # Check that found in database
    response: bool = utils.username_in_db(username=user_in_db.username)
    assert response


def test_username_in_db_false(client):
    """Verify return False if username is not in database."""
    # Define username
    username: str = "notindb"

    # Check that username is not in database
    user_in_db: models.User = db.session.query(models.User).filter_by(username=username).first()
    assert not user_in_db

    # Check that found in database
    response: bool = utils.username_in_db(username=username)
    assert not response


# get_username_or_request_ip


def test_get_username_or_request_ip_auth_current_user(client):
    """Verify that the correct user object is returned."""
    # Create new user
    username: str = "new_user_for_test"
    new_user: models.ResearchUser = models.ResearchUser(username=username, password="goodpassword")
    db.session.add(new_user)
    db.session.commit()

    # Authenticate user
    # auth.current_user() calls the following
    # ref: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/b42168ed174cde0a9404dbf0b05b5b5c5d6eb46d/src/flask_httpauth.py#L185-L187
    # def current_user(self):
    #     if hasattr(g, 'flask_httpauth_user'):
    #         return g.flask_httpauth_user
    flask.g.flask_httpauth_user = new_user

    # Call function
    response: str = utils.get_username_or_request_ip()
    assert response and response == new_user.username == username


def test_get_username_or_request_ip_flask_login_current_user(client):
    """Verify that the correct user object is returned."""
    # Get user
    user_object: models.User = db.session.query(models.User).first()
    assert user_object.is_authenticated

    # Login user
    flask_login.login_user(user_object)

    # Call function
    response: str = utils.get_username_or_request_ip()
    assert response and response == user_object.username


def test_get_username_or_request_ip_anonymous(client):
    """Verify that anonymous user is returned."""
    # Call function
    response: str = utils.get_username_or_request_ip()
    assert "(anonymous)" in response


def test_get_username_or_request_ip_remote_addr(client):
    """Verify that remote addr is returned"""
    flask.request.remote_addr = "http://localhost"
    assert flask.request.remote_addr == "http://localhost"
    # Call function
    response: str = utils.get_username_or_request_ip()
    assert "http://localhost" in response


# Access route test not implemented
# def test_get_username_or_request_ip_access_route(client):
#    pass


def test_delrequest_exists_true(client):
    """Verify deletion request row exists."""
    # Create deletion request
    user: models.User = db.session.query(models.User).first()
    deletion_request: models.DeletionRequest = models.DeletionRequest(
        email=user.primary_email, issued=utils.current_time()
    )
    user.deletion_request.append(deletion_request)
    db.session.commit()

    # Call function
    response: bool = utils.delrequest_exists(email=deletion_request.email)
    assert response


def test_delrequest_exists_false(client):
    """Check that deletion request does not exist."""
    # Define email
    email = "nosuchrequest@mail.com"

    # Create deletion request
    deletion_request: models.DeletionRequest = (
        db.session.query(models.DeletionRequest).filter_by(email=email).first()
    )
    assert not deletion_request

    # Run function
    response: bool = utils.delrequest_exists(email=email)
    assert not response


# send_reset_email


def test_send_reset_email(client):
    """Send reset email."""
    # Get email row
    email_row: models.Email = db.session.query(models.Email).first()

    # Run function
    with patch("dds_web.utils.mail.send"):
        response = utils.send_reset_email(email_row=email_row, token="")
    assert response is None


# send_project_access_reset_email


def test_send_project_access_reset_email(client):
    """Send project access reset email."""
    # Get email row
    email_row: models.Email = db.session.query(models.Email).first()

    # Call function
    with patch("dds_web.utils.mail.send"):
        response = utils.send_project_access_reset_email(
            email_row=email_row, email=email_row.email, token=None
        )
    assert response is None


# send email functions


def test_send_email_for_queue(client):
    """Send email for the queue function - ok first try."""
    # Get email row
    email_row: models.Email = db.session.query(models.Email).first()

    # Run function
    with patch("dds_web.utils.mail.send"):
        response = utils.send_email_for_queue(msg=email_row)
    assert response is None


def test_send_email_for_queue_exception(client):
    """Send email for the queue function - exception on the 1st try."""

    import smtplib

    side_effect = [smtplib.SMTPException, None]  # Exception on the first try, second try is ok

    # Get email row
    email_row: models.Email = db.session.query(models.Email).first()

    # Run function
    with patch("dds_web.utils.mail.send", side_effect=side_effect):
        response = utils.send_email_for_queue(msg=email_row)
    assert response is None


def test_send_email_with_retry(client):
    """Send email with retry ok first try."""
    # Get email row
    email_row: models.Email = db.session.query(models.Email).first()

    # Run function
    with patch("dds_web.utils.mail.send"):
        response = utils.send_email_with_retry(msg=email_row)
    assert response is None


def test_send_email_with_retry_exception(client):
    """Send email with retry - exception on the 1st try."""

    import smtplib

    side_effect = [smtplib.SMTPException, None]  # Exception on the first try, second try is ok

    # Get email row
    email_row: models.Email = db.session.query(models.Email).first()

    # Run function
    with patch("dds_web.utils.mail.send", side_effect=side_effect):
        response = utils.send_email_with_retry(msg=email_row)
    assert response is None


# is_safe_url - not tested
# def test_is_safe_url(client):
#     """Check if url is safe to redirect to."""

# current_time


def test_current_time():
    """Test getting the current time."""
    # Get current time
    current_time_manual = datetime.datetime.utcnow()

    # Call function
    current_time_from_function: datetime.datetime = utils.current_time()

    # Check that they are relatively close to each other
    assert current_time_manual < current_time_from_function
    assert current_time_from_function - datetime.timedelta(seconds=15) < current_time_manual
    assert isinstance(current_time_from_function, datetime.datetime)

    # tzinfo is None if in utc
    assert current_time_from_function.tzinfo is None


def test_current_time_to_midnight():
    """Test getting the current date, time: midnight."""
    # Get current time
    current_time_manual = datetime.datetime.utcnow()

    # Call function
    current_time_from_function: datetime.datetime = utils.current_time(to_midnight=True)

    # Check that correct time and date
    assert current_time_from_function.hour == 23
    assert current_time_from_function.minute == 59
    assert current_time_from_function.second == 59
    assert current_time_from_function.day == current_time_manual.day

    # tzinfo is None if in utc
    assert current_time_from_function.tzinfo is None


# timestamp


def add_zero_to_start(input: int, correct_length: int = 2):
    """Add a zero to each part of a timestamp."""
    return_string: str = str(input)
    field_length: int = len(str(input))
    if field_length < correct_length:
        return_string = str(0) + return_string

    return return_string


def test_timestamp():
    """Verify that timestamp is returned."""
    # Call function to create timestamp
    new_timestamp: str = utils.timestamp()
    assert isinstance(new_timestamp, str)


def test_timestamp_input_timestamp():
    """Check that function returns string representation of timestamp passed in."""
    # Get current time
    now: datetime.datetime = datetime.datetime.utcnow()

    # Call function
    datetime_string: str = utils.timestamp(dts=now)
    assert isinstance(datetime_string, str)
    assert (
        datetime_string
        == f"{add_zero_to_start(input=now.year, correct_length=4)}-{add_zero_to_start(input=now.month)}-{add_zero_to_start(input=now.day)} {add_zero_to_start(input=now.hour)}:{add_zero_to_start(input=now.minute)}:{add_zero_to_start(input=now.second)}.{add_zero_to_start(input=now.microsecond, correct_length=6)}"
    )


def test_timestamp_new_tsformat():
    """Verify that new format is applied."""
    # Get current time
    now: datetime.datetime = datetime.datetime.utcnow()

    # Call function
    datetime_string: str = utils.timestamp(dts=now, ts_format="%Y-%m")
    assert isinstance(datetime_string, str)
    assert (
        datetime_string
        == f"{add_zero_to_start(input=now.year, correct_length=4)}-{add_zero_to_start(input=now.month)}"
    )


def test_timestamp_datetime_string():
    """Check that year is returned when datetime string is entered."""
    # Get current time
    now: datetime.datetime = datetime.datetime.utcnow()

    # Call function
    datetime_string: str = utils.timestamp(dts=now)
    assert isinstance(datetime_string, str)

    # Call function again - real test
    new_datetime_string: str = utils.timestamp(datetime_string=datetime_string)
    assert (
        new_datetime_string
        == f"{add_zero_to_start(input=now.year, correct_length=4)}-{add_zero_to_start(input=now.month)}-{add_zero_to_start(input=now.day)}"
    )


# rate_limit_from_config


def test_rate_limit_from_config(client):
    """Test the limiter."""
    limit: str = utils.rate_limit_from_config()
    assert limit == "10/hour"


# working_directory


def test_working_directory(fs: FakeFilesystem):
    """Check that working directory has changed."""
    initial_path = os.getcwd()
    test_dir = "thisisatest"
    with utils.working_directory(path=test_dir):
        assert os.getcwd() == f"/{test_dir}"
    assert os.getcwd() == initial_path


# page_query


def test_page_query(client):
    """Test if paging works."""
    previous_projects = db.session.query(models.Project).count()

    # Create 1020 projects
    projects = [
        models.Project(
            public_id=f"project__{x}",
            title=f"{x} Project",
            description="This is a test project. You will be able to upload to but NOT download "
            "from this project. Create a new project to test the entire system. ",
            pi="support@example.com",
            bucket=f"testbucket_{x}",
        )
        for x in range(1020)
    ]
    assert len(projects) == 1020
    db.session.add_all(projects)
    db.session.commit()

    # Keep track of iterations
    iteration = 0

    # Run function
    for x in utils.page_query(db.session.query(models.Project)):
        iteration += 1

    assert iteration == (len(projects) + previous_projects)


# create_one_time_password_email


def test_create_one_time_password_email(client):
    """Test creating one time password email."""
    # User
    current_user: models.User = db.session.query(models.User).first()

    # Call function
    message: str = utils.create_one_time_password_email(user=current_user, hotp_value=b"012345")
    assert isinstance(message, flask_mail.Message)


# bucket_is_valid


def test_bucket_is_valid_too_short():
    """Test that a bucket name with length shorter than 3."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="bb")
    assert not valid
    assert "The bucket name has the incorrect length 2" in message


def test_bucket_is_valid_too_long():
    """Test that a bucket name with length longer than 63 is not valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="b" * 64)
    assert not valid
    assert "The bucket name has the incorrect length 64" in message


def test_bucket_is_valid_invalid_chars():
    """Test that a bucket name with underscore is not valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="bb_")
    assert not valid
    assert "The bucket name contains invalid characters." in message


def test_bucket_is_valid_begin_with_dot_or_dash():
    """Test that a bucket name beginning with a dot or a dash is not valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name=".bb")
    assert not valid
    assert "The bucket name must begin with a letter or number." in message

    # Call function again
    valid, message = utils.bucket_is_valid(bucket_name="-bb")
    assert not valid
    assert "The bucket name must begin with a letter or number." in message


def test_bucket_is_valid_too_many_dots():
    """Test that a bucket name with more than 2 dots is not valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="bb...")
    assert not valid
    assert "The bucket name cannot contain more than two dots." in message


def test_bucket_is_valid_invalid_prefix():
    """Test that a bucket name with prefix xn-- is not valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="xn--something")
    assert not valid
    assert "The bucket name cannot begin with the 'xn--' prefix." in message


def test_bucket_is_valid_invalid_suffix():
    """Test that a bucket name with suffix -s3alias is not valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="something-s3alias")
    assert not valid
    assert "The bucket name cannot end with the '-s3alias' suffix." in message


def test_bucket_is_valid_ok():
    """Test that a bucket name is valid."""
    # Call function
    valid, message = utils.bucket_is_valid(bucket_name="something-.")
    assert valid
    assert message == ""


# calculate usage


def test_calculate_bytehours_ok(client: flask.testing.FlaskClient):
    """Test that the float and function can handle a huge file stored for about 4 months."""
    minuend: datetime.datetime = datetime.datetime.utcnow()
    # simulate time_uploaded about 4 months ago = 2928.58 hours
    subtrahend = minuend - datetime.timedelta(hours=2928.58)

    # Call function
    bytehours = utils.calculate_bytehours(
        minuend=minuend, subtrahend=subtrahend, size_bytes=1000000000000000
    )
    assert type(bytehours) == float
    assert bytehours == 2.92858e18


def test_calculate_version_period_usage_existing_and_invoiced_version(
    client: flask.testing.FlaskClient,
):
    """Test that function returns correct value and resets time_invoiced."""
    now: datetime.datetime = datetime.datetime.utcnow()

    version = models.Version(
        size_stored=1,
        time_uploaded=now,
        time_invoiced=now - datetime.timedelta(hours=24),
    )

    time_invoiced_before = version.time_invoiced
    # Call function
    bytehours = utils.calculate_version_period_usage(version=version)
    assert round(bytehours) == 24.0
    assert version.time_invoiced != time_invoiced_before


def test_calculate_version_period_usage_deleted_and_not_invoiced_version(
    client: flask.testing.FlaskClient,
):
    """Test that function returns correct value and sets time_invoiced."""
    now: datetime.datetime = datetime.datetime.utcnow()

    version = models.Version(
        size_stored=1,
        time_uploaded=now - datetime.timedelta(hours=24),
        time_deleted=now - datetime.timedelta(hours=12),
    )

    # Call function
    bytehours = utils.calculate_version_period_usage(version=version)
    assert bytehours == 12.0
    assert version.time_invoiced


def test_calculate_version_period_usage_deleted_and_invoiced_version(
    client: flask.testing.FlaskClient,
):
    """Test that function returns correct value and sets correct time_invoiced."""
    now: datetime.datetime = datetime.datetime.utcnow()

    version = models.Version(
        size_stored=1,
        time_invoiced=now - datetime.timedelta(hours=24),
        time_deleted=now - datetime.timedelta(hours=12),
    )

    time_invoiced_before = version.time_invoiced
    # Call function
    bytehours = utils.calculate_version_period_usage(version=version)
    assert bytehours == 12.0
    assert version.time_invoiced != time_invoiced_before


def test_calculate_version_period_usage_new_version(client: flask.testing.FlaskClient):
    """Test that function returns correct value and sets time_invoiced."""
    existing_version = models.Version.query.first()

    # Call function
    bytehours = utils.calculate_version_period_usage(version=existing_version)
    assert existing_version.size_stored == 10000
    assert bytehours < 10000.0
    assert existing_version.time_invoiced


# format_timestamp


def test_format_timestamp_no_timestamp(client: flask.testing.FlaskClient):
    """No timestamp can be formatted if no timestamp is entered."""
    from dds_web.utils import format_timestamp

    timestamp = format_timestamp()
    assert timestamp is None


def test_format_timestamp_timestamp_object(client: flask.testing.FlaskClient):
    """Verify working timestamp object formatting."""
    from dds_web.utils import format_timestamp, current_time

    # 1. No passed in format
    # Verify that timestamp has a microseconds part
    now = current_time()
    assert now.microsecond != 0

    # Verify that timestamp does not have a microseconds part after formatting
    formatted = format_timestamp(timestamp_object=now)
    assert formatted.microsecond == 0

    # Verify that the two timestamps are not equal
    assert formatted != now

    # Verify that the timestamps have equal parts
    assert formatted.year == now.year
    assert formatted.month == now.month
    assert formatted.day == now.day
    assert formatted.hour == now.hour
    assert formatted.minute == now.minute
    assert formatted.second == now.second

    # 2. Passed in format
    # Verify that timestamp does not have minute, second or microsecond parts after formatting
    formatted_2 = format_timestamp(timestamp_object=now, timestamp_format="%Y-%m-%d %H")
    assert formatted_2.minute == 0
    assert formatted_2.second == 0
    assert formatted_2.microsecond == 0

    # Verify that the two timestamps are now equal
    # Verify that the two timestamps are not equal
    assert formatted_2 != now

    # Verify that the timestamps have equal parts
    assert formatted_2.year == now.year
    assert formatted_2.month == now.month
    assert formatted_2.day == now.day
    assert formatted_2.hour == now.hour


def test_format_timestamp_timestamp_string(client: flask.testing.FlaskClient):
    """Verify working timestamp string formatting."""
    from dds_web.utils import format_timestamp, current_time

    # 1. No passed in format
    now = current_time()
    now_as_string = now.strftime("%Y-%m-%d %H:%M:%S")

    # Verify that timestamp has a microseconds part
    assert now.microsecond != 0

    # # Verify that timestamp does not have a microseconds part after formatting
    formatted = format_timestamp(timestamp_string=now_as_string)
    assert formatted.microsecond == 0

    # Verify that the two timestamps are not equal
    assert formatted != now

    # Verify that the timestamps have equal parts
    assert formatted.year == now.year
    assert formatted.month == now.month
    assert formatted.day == now.day
    assert formatted.hour == now.hour
    assert formatted.minute == now.minute
    assert formatted.second == now.second

    # 2. Passed in format
    # Verify that timestamp does not have minute, second or microsecond parts after formatting
    with pytest.raises(ValueError) as err:
        format_timestamp(timestamp_string=now_as_string, timestamp_format="%H:%M:%S")
    assert (
        str(err.value)
        == "Timestamp strings need to contain year, month, day, hour, minute and seconds."
    )


# bytehours_in_last_month


def run_bytehours_test(client: flask.testing.FlaskClient, size_to_test: int):
    """Run checks to see that bytehours calc works."""
    # Imports
    from dds_web.utils import bytehours_in_last_month, current_time, format_timestamp

    # 1. 1 byte, 1 hour, since a month, not deleted --> 1 bytehour
    now = format_timestamp(timestamp_object=current_time())
    time_uploaded = now - datetime.timedelta(hours=1)
    expected_bytehour = size_to_test

    # 1a. Get version and change size stored
    version_to_test = models.Version.query.filter_by(time_deleted=None).first()
    version_to_test.size_stored = size_to_test
    version_to_test.time_uploaded = time_uploaded
    version_id = version_to_test.id
    db.session.commit()

    # 1b. Get same version
    version_to_test = models.Version.query.filter_by(id=version_id).first()
    assert version_to_test
    assert version_to_test.size_stored == size_to_test
    assert not version_to_test.time_deleted

    # 1c. Test bytehours
    bytehours = bytehours_in_last_month(version=version_to_test)

    # ---
    # 2. 1 byte, since 30 days, deleted 1 hour ago --> 1 bytehour
    time_deleted = now - datetime.timedelta(hours=1)
    time_uploaded = time_deleted - datetime.timedelta(hours=1)

    # 2a. Change time deleted to an hour ago and time uploaded to 2
    version_to_test.time_deleted = time_deleted
    version_to_test.time_uploaded = time_uploaded
    db.session.commit()

    # 2b. Get version again
    version_to_test = models.Version.query.filter_by(id=version_id).first()

    # 2c. Test bytehours
    bytehours = bytehours_in_last_month(version=version_to_test)
    assert int(bytehours) == expected_bytehour

    # ---
    # 3. 1 byte, before a month ago, not deleted --> 1*month
    now = format_timestamp(timestamp_object=current_time())
    time_uploaded = now - relativedelta(months=1, hours=1)
    time_a_month_ago = now - relativedelta(months=1)
    hours_since_month = (now - time_a_month_ago).total_seconds() / (60 * 60)
    expected_bytehour = size_to_test * hours_since_month

    # 3a. Change time uploaded and not deleted
    version_to_test.time_uploaded = time_uploaded
    version_to_test.time_deleted = None
    db.session.commit()

    # 3b. Get version again
    version_to_test = models.Version.query.filter_by(id=version_id).first()

    # 3c. Test bytehours
    bytehours = bytehours_in_last_month(version=version_to_test)
    assert bytehours == expected_bytehour

    # ---
    # 4. 1 byte, before 30 days, deleted an hour ago --> 1 hour less than a month
    time_deleted = format_timestamp(timestamp_object=current_time()) - relativedelta(hours=1)
    time_uploaded = now - relativedelta(months=1, hours=1)
    time_a_month_ago = now - relativedelta(months=1)
    hours_since_month = (time_deleted - time_a_month_ago).total_seconds() / (60 * 60)
    expected_bytehour = size_to_test * hours_since_month

    # 4a. Change time deleted and uploaded
    version_to_test.time_uploaded = time_uploaded
    version_to_test.time_deleted = time_deleted
    db.session.commit()

    # 4b. Get version again
    version_to_test = models.Version.query.filter_by(id=version_id).first()

    # 4c. Test bytehours
    bytehours = bytehours_in_last_month(version=version_to_test)
    assert int(bytehours) == expected_bytehour


def test_bytehours_in_last_month_1byte(client: flask.testing.FlaskClient):
    """Test that function calculates the correct number of TBHours."""
    run_bytehours_test(client=client, size_to_test=1)


def test_bytehours_in_last_month_1tb(client: flask.testing.FlaskClient):
    """Test that function calculates the correct number of TBHours."""
    run_bytehours_test(client=client, size_to_test=1e12)


def test_bytehours_in_last_month_20tb(client: flask.testing.FlaskClient):
    """Test that function calculates the correct number of TBHours."""
    run_bytehours_test(client=client, size_to_test=20 * 1e12)


# list_lost_files_in_project


def test_list_lost_files_in_project_nosuchbucket(
    client: flask.testing.FlaskClient, boto3_session, capfd
):
    """Verify that nosuchbucket error is raised and therefore message printed."""
    # Imports
    from dds_web.utils import list_lost_files_in_project

    # Get project
    project = models.Project.query.first()
    assert project

    # Mock NoSuchBucket error
    with patch("boto3.session.Session.resource.meta.client.head_bucket", mock_nosuchbucket):
        # Verify that exception is raised
        with pytest.raises(botocore.exceptions.ClientError):
            in_db_but_not_in_s3, in_s3_but_not_in_db = list_lost_files_in_project(
                project=project, s3_resource=boto3_session
            )
            assert not in_db_but_not_in_s3
            assert not in_s3_but_not_in_db

        # Verify that correct messages is printed
        _, err = capfd.readouterr()
        assert f"Project '{project.public_id}' bucket is missing" in err
        assert f"Expected: {not project.is_active}" in err


def test_list_lost_files_in_project_nothing_in_s3(
    client: flask.testing.FlaskClient, boto3_session, capfd
):
    """Verify that all files in db are printed since they do not exist in s3."""
    # Imports
    from dds_web.utils import list_lost_files_in_project

    # Get project
    project = models.Project.query.first()
    assert project

    # Run listing
    in_db_but_not_in_s3, in_s3_but_not_in_db = list_lost_files_in_project(
        project=project, s3_resource=boto3_session
    )

    # Verify that in_s3_but_not_db is empty
    assert not in_s3_but_not_in_db

    # Get logging
    _, err = capfd.readouterr()

    # Verify that all files are listed
    for f in project.files:
        assert f.name_in_bucket in in_db_but_not_in_s3
        assert (
            f"Entry {f.name_in_bucket} ({project.public_id}, {project.responsible_unit}) not found in S3 (but found in db)"
            in err
        )
        assert (
            f"Entry {f.name_in_bucket} ({project.public_id}, {project.responsible_unit}) not found in database (but found in s3)"
            not in err
        )


def test_list_lost_files_in_project_s3anddb_empty(
    client: flask.testing.FlaskClient, boto3_session, capfd
):
    """Verify that there are no lost files because there are no files."""
    # Imports
    from dds_web.utils import list_lost_files_in_project

    # Get project
    project = models.Project.query.first()
    assert project

    # Mock project.files -- no files
    with patch("dds_web.database.models.Project.files", new_callable=PropertyMock) as mock_files:
        mock_files.return_value = []

        # Run listing
        in_db_but_not_in_s3, in_s3_but_not_in_db = list_lost_files_in_project(
            project=project, s3_resource=boto3_session
        )

        # Verify that both are empty
        assert not in_db_but_not_in_s3
        assert not in_s3_but_not_in_db

    # Get logging output
    _, err = capfd.readouterr()

    # Verify no message printed out
    assert not err


def test_list_lost_files_in_project_no_files_in_db(
    client: flask.testing.FlaskClient, boto3_session, capfd
):
    """Mock files in s3 and verify that only those are printed out."""
    # Imports
    from dds_web.utils import list_lost_files_in_project

    # Get project
    project = models.Project.query.first()
    assert project

    # Mock project.files -- no files
    with patch("dds_web.database.models.Project.files", new_callable=PropertyMock) as mock_files:
        mock_files.return_value = []

        # Mock files in s3
        boto3_session.Bucket(project.bucket).objects.all = mock_items_in_bucket
        # Get created testfiles
        fake_files_in_bucket = mock_items_in_bucket()

        # Run listing
        in_db_but_not_in_s3, in_s3_but_not_in_db = list_lost_files_in_project(
            project=project, s3_resource=boto3_session
        )

        # Verify that missing in database but exists in s3
        assert not in_db_but_not_in_s3
        assert in_s3_but_not_in_db

    # Get logging
    _, err = capfd.readouterr()

    # Verify that all fake files are printed out
    for x in fake_files_in_bucket:
        assert (
            f"Entry {x.key} ({project.public_id}, {project.responsible_unit}) not found in database (but found in s3)"
            in err
        )

    # Verify that no file lines are printed out
    for x in project.files:
        assert (
            f"Entry {x.name_in_bucket} ({project.public_id}, {project.responsible_unit}) not found in S3 (but found in db)"
            not in err
        )


def test_list_lost_files_in_project_overlap(
    client: flask.testing.FlaskClient, boto3_session, capfd
):
    """Verify that only some files are printed out when some files exist in the database and s3, but not all."""
    # Imports
    from dds_web.utils import list_lost_files_in_project

    # Get project
    project = models.Project.query.first()
    assert project

    # Get created testfiles
    fake_files_in_bucket = mock_items_in_bucket()

    # Number of project files
    original_db_files = project.files
    num_proj_files = len(original_db_files)

    # Create 15 few new files
    new_files = []
    for x in fake_files_in_bucket[:15]:
        new_file = models.File(
            name=x.key,
            name_in_bucket=x.key,
            subpath=".",
            size_original=0,
            size_stored=0,
            compressed=True,
            public_key="X" * 64,
            salt="X" * 32,
            checksum="X" * 64,
        )
        new_files.append(new_file)
        project.files.append(new_file)
    db.session.commit()

    # Mock files in s3
    boto3_session.Bucket(project.bucket).objects.all = mock_items_in_bucket

    # Run listing
    in_db_but_not_in_s3, in_s3_but_not_in_db = list_lost_files_in_project(
        project=project, s3_resource=boto3_session
    )

    # Verify that both contain entries
    assert in_db_but_not_in_s3
    assert in_s3_but_not_in_db

    # Get logging output
    _, err = capfd.readouterr()

    # Verify that original db files are printed
    assert len(project.files) == num_proj_files + 15
    for x in project.files:
        if x not in new_files:
            assert (
                f"Entry {x.name_in_bucket} ({project.public_id}, {project.responsible_unit}) not found in S3 (but found in db)"
                in err
            )

    # Verify that s3 files are printed
    for x in fake_files_in_bucket[15::]:
        assert (
            f"Entry {x.key} ({project.public_id}, {project.responsible_unit}) not found in database (but found in s3)"
            in err
        )

    # Verify that the rest of the files are not printed
    for x in fake_files_in_bucket[:15]:
        assert (
            f"Entry {x.key} ({project.public_id}, {project.responsible_unit}) not found in S3 (but found in db)"
            not in err
        )
        assert (
            f"Entry {x.key} ({project.public_id}, {project.responsible_unit}) not found in database (but found in s3)"
            not in err
        )


def test_list_lost_files_in_project_sql_error(
    client: flask.testing.FlaskClient, boto3_session, capfd
):
    """Verify proper behaviour when sql OperationalError occurs."""
    # Imports
    from dds_web.utils import list_lost_files_in_project
    from sqlalchemy.exc import OperationalError

    # Get project
    project = models.Project.query.first()
    assert project

    # Mock files in s3
    boto3_session.Bucket(project.bucket).objects.all = mock_items_in_bucket
    # Get created testfiles
    fake_files_in_bucket = mock_items_in_bucket()

    # mock db.session.commit
    files_name_in_bucket_mock = PropertyMock(
        side_effect=sqlalchemy.exc.OperationalError("OperationalError", "test", "sqlalchemy")
    )

    # Run listing
    with patch("dds_web.database.models.Project.files", files_name_in_bucket_mock):
        try:
            in_db_but_not_in_s3, in_s3_but_not_in_db = list_lost_files_in_project(
                project=project, s3_resource=boto3_session
            )
        except OperationalError as e:
            print(f"OperationalError occurred: {e}")

    # Get logging output
    out, err = capfd.readouterr()
    assert "OperationalError occurred" in out
    assert "Unable to connect to db" in err


# use_sto4


def test_use_sto4_return_false(client: flask.testing.FlaskClient):
    """Test that use_sto4 returns False."""
    # Imports
    from dds_web.utils import use_sto4, current_time
    from dds_web.errors import S3InfoNotFoundError

    # Return False if sto4_start_time not set --------------------------
    # Get project
    project: models.Project = models.Project.query.first()

    # Get unit
    unit: models.Unit = project.responsible_unit
    assert not unit.sto4_start_time

    # Run function
    result: bool = use_sto4(unit_object=unit, project_object=project)
    assert result is False
    # -------------------------------------------------------------------

    # Return False if sto4_start_time is set, but project created before
    # Set sto4_start_time
    unit.sto4_start_time = current_time()
    db.session.commit()

    # Verify
    assert project.date_created < unit.sto4_start_time

    # Run function
    result: bool = use_sto4(unit_object=unit, project_object=project)
    assert result is False
    # -------------------------------------------------------------------

    # Return False if sto4_start_time is set, project created after,
    # but not all variables are set
    unit.sto4_start_time = current_time() - relativedelta(hours=1)
    db.session.commit()

    # Verify
    assert project.date_created > unit.sto4_start_time

    # Run function
    with pytest.raises(S3InfoNotFoundError) as err:
        result: bool = use_sto4(unit_object=unit, project_object=project)
        assert result is False
    assert f"One or more sto4 variables are missing for unit {unit.public_id}." in str(err.value)
    # -------------------------------------------------------------------


def test_use_sto4_return_true(client: flask.testing.FlaskClient):
    """Test that use_sto4 returns False."""
    # Imports
    from dds_web.utils import use_sto4, current_time

    # Get project
    project: models.Project = models.Project.query.first()

    # Unit
    unit: models.Unit = project.responsible_unit

    # Return True if sto4_start_time is set,
    # project is created after sto4_start_time was added,
    # and all variables are set
    unit.sto4_start_time = current_time() - relativedelta(hours=1)
    unit.sto4_endpoint = "endpoint"
    unit.sto4_name = "name"
    unit.sto4_access = "access"
    unit.sto4_secret = "secret"
    db.session.commit()

    # Run function
    result: bool = use_sto4(unit_object=unit, project_object=project)
    assert result is True


# add_uploaded_files_to_db


def test_add_uploaded_files_to_db_other_failed_op(client: flask.testing.FlaskClient):
    """Test calling the function with "failed_op" other than "add_file_db"."""
    # Prepare input data
    proj_in_db = models.Project.query.first()
    log = {
        "file1.txt": {
            "status": {"failed_op": "some_other_failed_op"},
            "path_remote": "path/to/file1.txt",
            "subpath": "subpath",
            "size_raw": 100,
            "size_processed": 200,
            "compressed": False,
            "public_key": "public_key",
            "salt": "salt",
            "checksum": "checksum",
        }
    }

    # Mock the S3 connector and head_object method
    mock_s3conn = MagicMock()
    mock_s3conn.resource.meta.client.head_object.return_value = None

    # Call the function
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", return_value=mock_s3conn):
        files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that the file is added to the database
    file = models.File.query.filter_by(name="file1.txt").first()
    assert not file

    # check that the error is returned and files_added is empty
    assert file not in files_added
    assert files_added == []

    assert "Incorrect 'failed_op'." in errors["file1.txt"]["error"]


def test_add_uploaded_files_to_db_correct_failed_op_file_not_found_in_s3(
    client: flask.testing.FlaskClient,
):
    """Test the return values of the function when file is not found on S3."""
    from botocore.exceptions import ClientError

    # Prepare input data
    proj_in_db = models.Project.query.first()
    log = {
        "file1.txt": {
            "status": {"failed_op": "add_file_db"},
            "path_remote": "path/to/file1.txt",
            "subpath": "subpath",
            "size_raw": 100,
            "size_processed": 200,
            "compressed": False,
            "public_key": "public_key",
            "salt": "salt",
            "checksum": "checksum",
        }
    }

    # mock ApiS3Connector
    mock_api_s3_conn = MagicMock()
    mock_s3conn = mock_api_s3_conn.return_value.__enter__.return_value

    # call add_uploaded_files_to_db
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", mock_api_s3_conn):
        mock_s3conn.resource.meta.client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "operation_name"
        )
        files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that the file is not added to the database
    file = models.File.query.filter_by(name="file1.txt").first()
    assert not file

    # check that the error is returned and files_added is empty
    assert file not in files_added
    assert files_added == []
    assert "File not found in S3" in errors["file1.txt"]["error"]


def test_add_uploaded_files_to_db_correct_failed_op_file_not_found_in_db(
    client: flask.testing.FlaskClient,
):
    """Test calling the function with correct "failed_op" and file isn't found in database."""
    # Mock input data
    proj_in_db = models.Project.query.first()
    file_name = "file1.txt"
    log = {
        file_name: {
            "status": {"failed_op": "add_file_db"},
            "path_remote": f"path/to/{file_name}",
            "subpath": "subpath",
            "size_raw": 100,
            "size_processed": 200,
            "compressed": False,
            "public_key": "public_key",
            "salt": "salt",
            "checksum": "checksum",
        }
    }

    # Verify that file does not exist
    file_object = models.File.query.filter(
        sqlalchemy.and_(
            models.File.name == sqlalchemy.func.binary(file_name),
            models.File.project_id == proj_in_db.id,
        )
    ).first()
    assert not file_object

    # Mock the S3 connector and head_object method
    mock_s3conn = MagicMock()
    mock_s3conn.resource.meta.client.head_object.return_value = None

    # Call the function
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", return_value=mock_s3conn):
        files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that the file is added to the database
    file = models.File.query.filter(
        sqlalchemy.and_(
            models.File.name == sqlalchemy.func.binary(file_name),
            models.File.project_id == proj_in_db.id,
        )
    ).first()
    assert file
    assert file.name == file_name
    assert file.name_in_bucket == log[file_name]["path_remote"]
    assert file.subpath == log[file_name]["subpath"]
    assert file.size_original == log[file_name]["size_raw"]
    assert file.size_stored == log[file_name]["size_processed"]
    assert file.compressed != log[file_name]["compressed"]
    assert file.public_key == log[file_name]["public_key"]
    assert file.salt == log[file_name]["salt"]
    assert file.checksum == log[file_name]["checksum"]

    # Check that the file is added to the project
    assert file in proj_in_db.files

    # Check that the version is added to the database
    version = models.Version.query.filter_by(active_file=file.id).first()
    assert version
    assert version.size_stored == log[file_name]["size_processed"]

    # Check the return values
    assert file in files_added
    assert errors == {}


def test_add_uploaded_files_to_db_correct_failed_op_file_is_found_in_db_no_overwrite(
    client: flask.testing.FlaskClient,
):
    """Test calling the function with correct "failed_op" and file IS found in database."""
    # Mock input data
    proj_in_db = models.Project.query.first()
    file_name = "file1.txt"
    log = {
        file_name: {
            "status": {"failed_op": "add_file_db"},
            "path_remote": f"path/to/{file_name}",
            "subpath": "subpath",
            "size_raw": 100,
            "size_processed": 200,
            "compressed": False,
            "public_key": "public_key",
            "salt": "salt",
            "checksum": "checksum",
        }
    }

    # Create new file
    new_file = models.File(
        name=file_name,
        name_in_bucket=log[file_name]["path_remote"],
        subpath=log[file_name]["subpath"],
        size_original=log[file_name]["size_raw"],
        size_stored=log[file_name]["size_processed"],
        compressed=not log[file_name]["compressed"],
        public_key=log[file_name]["public_key"],
        salt=log[file_name]["salt"],
        checksum=log[file_name]["checksum"],
    )
    proj_in_db.files.append(new_file)
    db.session.add(new_file)
    db.session.commit()

    # Mock the S3 connector and head_object method
    mock_s3conn = MagicMock()
    mock_s3conn.resource.meta.client.head_object.return_value = None

    # Call the function
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", return_value=mock_s3conn):
        files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that the error is returned and files_added is empty
    assert files_added == []
    assert "File already in database" in errors[file_name]["error"]

    # Check that the version is not added to the database
    version = models.Version.query.filter_by(active_file=new_file.id).first()
    assert not version


def test_add_uploaded_files_to_db_correct_failed_op_file_is_found_in_db_overwrite_missing_key(
    client: flask.testing.FlaskClient,
):
    """Test calling the function with correct "failed_op" and file IS found in database but there's at least one key missing."""
    # Mock input data
    proj_in_db = models.Project.query.first()
    file_name = "file1.txt"
    log = {
        file_name: {
            "status": {"failed_op": "add_file_db"},
            "path_remote": f"path/to/{file_name}",
            "subpath": "subpath",
            "size_raw": 100,
            "size_processed": 200,
            "compressed": False,
            "public_key": "public_key",
            "salt": "salt",
            "checksum": "checksum",
            "overwrite": True,
        }
    }

    # Create new file
    new_file = models.File(
        name=file_name,
        name_in_bucket=log[file_name]["path_remote"],
        subpath=log[file_name]["subpath"],
        size_original=log[file_name]["size_raw"],
        size_stored=log[file_name]["size_processed"],
        compressed=not log[file_name]["compressed"],
        public_key=log[file_name]["public_key"],
        salt=log[file_name]["salt"],
        checksum=log[file_name]["checksum"],
    )
    proj_in_db.files.append(new_file)
    db.session.add(new_file)
    db.session.commit()

    # Mock the S3 connector and head_object method
    mock_s3conn = MagicMock()
    mock_s3conn.resource.meta.client.head_object.return_value = None

    # Remove key
    log[file_name].pop("checksum")

    # Call the function
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", return_value=mock_s3conn):
        files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that the error is returned and files_added is empty
    assert files_added == []
    assert "Missing key: 'checksum'" in errors[file_name]["error"]

    # Check that the version is not added to the database
    version = models.Version.query.filter_by(active_file=new_file.id).first()
    assert not version


def test_add_uploaded_files_to_db_correct_failed_op_file_is_found_in_db_overwrite_ok(
    client: flask.testing.FlaskClient,
):
    """Test calling the function with correct "failed_op" and file IS found in database but overwrite is specified."""
    # Mock input data
    proj_in_db = models.Project.query.first()
    file_name = "file1.txt"
    original_file_info = {
        "name": file_name,
        "path_remote": f"path/to/{file_name}",
        "subpath": "subpath",
        "size_raw": 100,
        "size_processed": 200,
        "compressed": False,
        "public_key": "public_key",
        "salt": "salt",
        "checksum": "checksum",
    }
    log = {
        file_name: {
            "status": {"failed_op": "add_file_db"},
            "path_remote": f"path/to/{file_name}",
            "subpath": "subpath2",
            "size_raw": 1001,
            "size_processed": 201,
            "compressed": True,
            "public_key": "public_key2",
            "salt": "salt2",
            "checksum": "checksum2",
            "overwrite": True,
        }
    }

    # Create new file
    new_file = models.File(
        name=file_name,
        name_in_bucket=original_file_info["path_remote"],
        subpath=original_file_info["subpath"],
        size_original=original_file_info["size_raw"],
        size_stored=original_file_info["size_processed"],
        compressed=original_file_info["compressed"],
        public_key=original_file_info["public_key"],
        salt=original_file_info["salt"],
        checksum=original_file_info["checksum"],
    )
    proj_in_db.files.append(new_file)
    db.session.add(new_file)
    db.session.commit()

    # Mock the S3 connector and head_object method
    mock_s3conn = MagicMock()
    mock_s3conn.resource.meta.client.head_object.return_value = None

    # Call the function
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", return_value=mock_s3conn):
        files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that no error is returned and that there's a file and version added
    file = models.File.query.filter(
        sqlalchemy.and_(
            models.File.name == sqlalchemy.func.binary(file_name),
            models.File.project_id == proj_in_db.id,
        )
    ).first()
    assert file
    assert file.name == file_name
    assert file.name_in_bucket == log[file_name]["path_remote"]
    assert file.subpath == log[file_name]["subpath"]
    assert file.size_original == log[file_name]["size_raw"]
    assert file.size_stored == log[file_name]["size_processed"]
    assert file.compressed != log[file_name]["compressed"]
    assert file.public_key == log[file_name]["public_key"]
    assert file.salt == log[file_name]["salt"]
    assert file.checksum == log[file_name]["checksum"]
    assert files_added and file in files_added

    assert errors == {}

    # Check that the version is added to the database
    version = models.Version.query.filter_by(active_file=new_file.id).first()
    assert version
    assert version.size_stored == file.size_stored


def test_add_uploaded_files_to_db_sql_error(client: flask.testing.FlaskClient):
    """Test the return values of the function when sqlalchemy error occurs."""
    import sqlalchemy.exc
    from dds_web import db

    # Prepare input data
    proj_in_db = models.Project.query.first()
    log = {
        "file1.txt": {
            "status": {"failed_op": "add_file_db"},
            "path_remote": "path/to/file1.txt",
            "subpath": "subpath",
            "size_raw": 100,
            "size_processed": 200,
            "compressed": False,
            "public_key": "public_key",
            "salt": "salt",
            "checksum": "checksum",
        }
    }

    # mock ApiS3Connector
    mock_s3conn = MagicMock()
    mock_s3conn.resource.meta.client.head_object.return_value = None

    # mock db.session.commit
    db_session_commit_mock = MagicMock(
        side_effect=sqlalchemy.exc.OperationalError("OperationalError", "test", "sqlalchemy")
    )

    # call add_uploaded_files_to_db
    with patch("dds_web.api.api_s3_connector.ApiS3Connector", return_value=mock_s3conn):
        with patch("dds_web.db.session.commit", db_session_commit_mock):
            files_added, errors = utils.add_uploaded_files_to_db(proj_in_db, log)

    # check that the file is not added to the database
    file = models.File.query.filter_by(name="file1.txt").first()
    assert not file

    # check that the error is returned and files_added is empty
    assert file not in files_added
    assert files_added == []
    assert "OperationalError" in errors["file1.txt"]["error"]


# new_file_version


def test_new_file_version_multiple_versions(
    client: flask.testing.FlaskClient, capfd: LogCaptureFixture
):
    """If there are multiple versions for the same file then they should be updated identically."""
    # Get any project
    project = models.Project.query.first()

    # Define file info
    file_name = "file1.txt"
    original_file_info = {
        "name": file_name,
        "path_remote": f"path/to/{file_name}",
        "subpath": "subpath",
        "size_raw": 100,
        "size_processed": 200,
        "compressed": False,
        "public_key": "public_key",
        "salt": "salt",
        "checksum": "checksum",
    }

    # Create new file
    new_file = models.File(
        name=file_name,
        name_in_bucket=original_file_info["path_remote"],
        subpath=original_file_info["subpath"],
        size_original=original_file_info["size_raw"],
        size_stored=original_file_info["size_processed"],
        compressed=original_file_info["compressed"],
        public_key=original_file_info["public_key"],
        salt=original_file_info["salt"],
        checksum=original_file_info["checksum"],
    )

    # Create new versions (multiple) of the file
    new_version_1 = models.Version(
        size_stored=original_file_info["size_processed"],
        time_uploaded=utils.current_time(),
        active_file=new_file.id,
        project_id=project,
    )
    new_version_2 = models.Version(
        size_stored=original_file_info["size_processed"] + 10,
        time_uploaded=utils.current_time(),
        active_file=new_file.id,
        project_id=project,
    )

    # Append to relationships
    project.files.append(new_file)
    project.file_versions.extend([new_version_1, new_version_2])
    new_file.versions.extend([new_version_1, new_version_2])

    db.session.add(new_file)
    db.session.commit()

    # Define new file info
    new_file_info = {
        "name": file_name,
        "path_remote": f"path/to/{file_name}",
        "subpath": "subpath",
        "size_raw": 1001,
        "size_processed": 2001,
        "compressed": True,
        "public_key": "public_key2",
        "salt": "salt2",
        "checksum": "checksum2",
    }

    # Run function
    utils.new_file_version(existing_file=new_file, new_info=new_file_info)

    # Verify that logging printed
    _, err = capfd.readouterr()
    assert (
        "There is more than one version of the file which does not yet have a deletion timestamp."
        in err
    )

    # Verify that there's a new version
    assert len(new_file.versions) == 3

    # Verify that the file info has been updated
    assert new_file.subpath == new_file_info["subpath"] == original_file_info["subpath"]
    assert new_file.size_original == new_file_info["size_raw"] != original_file_info["size_raw"]
    assert (
        new_file.size_stored
        == new_file_info["size_processed"]
        != original_file_info["size_processed"]
    )
    assert (
        new_file.compressed
        == (not new_file_info["compressed"])
        != (not original_file_info["compressed"])
    )
    assert new_file.salt == new_file_info["salt"] != original_file_info["salt"]
    assert new_file.public_key == new_file_info["public_key"] != original_file_info["public_key"]
    assert new_file.time_uploaded != new_version_1.time_deleted == new_version_2.time_deleted
    assert new_file.checksum == new_file_info["checksum"] != original_file_info["checksum"]
