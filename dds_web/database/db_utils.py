""" Utility function that makes DB calls """

from dds_web import db
from dds_web.database import models


def get_facility_column(fid, column) -> (str):
    """Gets the columns value from DB for given facility ID"""
    facility = models.Facility.query.filter_by(id=fid).first()
    return getattr(facility, column)


def get_facility_column_by_username(fname, column) -> (str):
    """Gets the columns value from DB for given facility username"""
    facility = models.Facility.query.filter_by(username=fname).first()
    return getattr(facility, column)


def get_facilty_projects(fid, only_id=False) -> (list):
    """Gets all the project for the facility ID"""
    project_list = models.Project.query.filter_by(facility_id=fid).all()
    return project_list if not only_id else [prj.id for prj in project_list]


def get_user_column_by_username(username, column) -> (str):
    """Gets the columns value from DB for given username"""
    user = models.User.query.filter_by(username=username).first()
    return getattr(user, column)


def get_user_projects(uid, only_id=False) -> (list):
    """Gets all the project for the username ID"""
    # project_list = models.Project.query.filter_by(owner=uid).all()
    project_list = db.session.query(models.project_users).filter_by(user_id=uid).all()
    project_ids = [prj.project_id for prj in project_list]
    return (
        project_ids
        if only_id
        else models.Project.query.filter(models.Project.id.in_(project_ids)).all()
    )


def get_project_users(project_id, no_facility_users=False) -> (list):
    """Get list of users related to the project"""
    project_users = []
    project_user_rows = (
        db.session.query(models.project_users).filter_by(project_id=project_id).all()
    )
    for row in project_user_rows:
        user = models.User.query.filter_by(id=row.user_id).one()
        if no_facility_users and (user.role != "researcher"):
            continue
        project_users.append(user.username)
    return project_users


def get_full_column_from_table(table, column) -> (list):
    """Get the whole column from the given table"""
    mtable = getattr(models, table)
    return [entry[0] for entry in mtable.query.with_entities(getattr(mtable, column)).all()]


def get_user_emails(uid, only_id=False) -> (list):
    """Gets all the email addresses for the user ID"""
    email_list = models.Email.query.filter_by(user_id=uid).all()
    return email_list if not only_id else [email.id for email in email_list]
