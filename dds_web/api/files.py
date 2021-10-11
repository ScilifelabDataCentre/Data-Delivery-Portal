"""Files module."""

####################################################################################################
# IMPORTS ################################################################################ IMPORTS #
####################################################################################################

# Standard library
import os

# Installed
import flask_restful
import flask
import sqlalchemy
from sqlalchemy.sql import func

# Own modules
import dds_web.utils
from dds_web import auth
from dds_web.database import models
from dds_web import db
from dds_web.api.api_s3_connector import ApiS3Connector
from dds_web.api.db_connector import DBConnector
from dds_web.api.errors import DatabaseError
from dds_web.api import marshmallows

####################################################################################################
# ENDPOINTS ############################################################################ ENDPOINTS #
####################################################################################################


class NewFile(flask_restful.Resource):
    """Inserts a file into the database"""

    @auth.login_required(role=["Unit Personnel", "Unit Admin", "Super Admin"])
    def post(self):
        """Add new file to DB."""

        new_file = marshmallows.NewFileSchema().load({**flask.request.json, **flask.request.args})

        try:
            db.session.commit()
        except sqlalchemy.exc.SQLAlchemyError as err:
            flask.current_app.logger.debug(err)
            db.session.rollback()
            return flask.make_response(f"Failed to add new file to database.", 500)

        return flask.jsonify({"message": f"File '{new_file.name}' added to db."})

    @auth.login_required(role=["Unit Personnel", "Unit Admin", "Super Admin"])
    def put(self):

        new_version = marshmallows.NewVersionSchema().load(
            {**flask.request.json, **flask.request.args}
        )

        try:
            db.session.commit()
        except sqlalchemy.exc.SQLAlchemyError as err:
            flask.current_app.logger.debug(err)
            db.session.rollback()
            return flask.make_response(f"Failed updating file information.", 500)

        return flask.jsonify({"message": f"File '{flask.request.json.get('name')}' updated in db."})


class MatchFiles(flask_restful.Resource):
    """Checks for matching files in database"""

    @auth.login_required(role=["Unit Personnel", "Unit Admin", "Super Admin"])
    def get(self):
        """Matches specified files to files in db."""

        files = marshmallows.MatchFilesSchema().load(flask.request.args)

        return flask.jsonify(
            {"files": {f.name: f.name_in_bucket for f in files} if files else None}
        )


class ListFiles(flask_restful.Resource):
    """Lists files within a project"""

    @auth.login_required
    def get(self):
        """Get a list of files within the specified folder."""

        distinct_files, distinct_folders = marshmallows.FileSchema().load(flask.request.args)

        files_folders = list()
        subpath = flask.request.args.get("subpath")
        show_size = flask.request.args.get("show_size")

        # Collect file and folder info to return to CLI
        if distinct_files:
            for x in distinct_files:
                info = {
                    "name": x[0] if subpath == "." else x[0].split(os.sep)[-1],
                    "folder": False,
                }
                if show_size:
                    info.update({"size": dds_web.utils.format_byte_size(x[1])})
                files_folders.append(info)
        if distinct_folders:
            for x in distinct_folders:
                info = {
                    "name": x if subpath == "." else x.split(os.sep)[-1],
                    "folder": True,
                }

                if show_size:
                    try:
                        folder_size = dds_web.utils.folder_size(folder_name=x)
                    except DatabaseError:
                        raise

                    info.update({"size": dds_web.utils.format_byte_size(folder_size)})
                files_folders.append(info)

        return flask.jsonify({"files_folders": files_folders})


class RemoveFile(flask_restful.Resource):
    """Removes files from the database and s3 with boto3."""

    @auth.login_required(role=["Unit Personnel", "Unit Admin", "Super Admin"])
    def delete(self):
        """Deletes the files"""

        project = marshmallows.ProjectRequiredSchema().load(flask.request.args)

        not_removed_dict, not_exist_list, error = dds_web.utils.delete_multiple(
            project=project, files=flask.request.json
        )

        # S3 connection error
        if not any([not_removed_dict, not_exist_list]) and error != "":
            return flask.make_response(error, 500)

        # Return deleted and not deleted files
        return flask.jsonify({"not_removed": not_removed_dict, "not_exists": not_exist_list})


class RemoveDir(flask_restful.Resource):
    """Removes one or more full directories from the database and s3."""

    @auth.login_required(role=["Unit Personnel", "Unit Admin", "Super Admin"])
    def delete(self):
        """Deletes the folders."""

        project = marshmallows.ProjectRequiredSchema().load(flask.request.args)

        not_removed_dict, not_exist_list = ({}, [])

        try:
            with ApiS3Connector() as s3conn:
                # Error if not enough info
                if None in [s3conn.url, s3conn.keys, s3conn.bucketname]:
                    return (
                        not_removed_dict,
                        not_exist_list,
                        "No s3 info returned! " + s3conn.message,
                    )

                for x in flask.request.json:
                    # Get all files in the folder
                    in_db, folder_deleted, error = dds_web.utils.delete_folder(folder=x)

                    if not in_db:
                        db.session.rollback()
                        not_exist_list.append(x)
                        continue

                    # Error with db --> folder error
                    if not folder_deleted:
                        db.session.rollback()
                        not_removed_dict[x] = error
                        continue

                    # Delete from s3
                    folder_deleted, error = s3conn.remove_folder(folder=x)

                    if not folder_deleted:
                        db.session.rollback()
                        not_removed_dict[x] = error
                        continue

                    # Commit to db if no error so far
                    try:
                        db.session.commit()
                    except sqlalchemy.exc.SQLAlchemyError as err:
                        db.session.rollback()
                        not_removed_dict[x] = str(err)
                        continue
        except (ValueError,):
            raise
        return flask.jsonify({"not_removed": not_removed_dict, "not_exists": not_exist_list})


class FileInfo(flask_restful.Resource):
    """Get file info on files to download."""

    @auth.login_required
    def get(self):
        """Checks which files can be downloaded, and get their info."""

        project = marshmallows.ProjectRequiredSchema().load(flask.request.args)

        # Get files and folders requested by CLI
        paths = flask.request.json

        files_single, files_in_folders = ({}, {})

        # Get info on files and folders
        try:
            # Get all files in project
            files_in_proj = models.File.query.filter(
                models.File.project_id == func.binary(project.id)
            )

            # All files matching the path -- single files
            files = (
                files_in_proj.filter(models.File.name.in_(paths))
                .with_entities(
                    models.File.name,
                    models.File.name_in_bucket,
                    models.File.subpath,
                    models.File.size_original,
                    models.File.size_stored,
                    models.File.salt,
                    models.File.public_key,
                    models.File.checksum,
                    models.File.compressed,
                )
                .all()
            )

            # All paths which start with the subpath are within a folder
            for x in paths:
                # Only try to match those not already saved in files
                if x not in [f[0] for f in files]:
                    list_of_files = (
                        files_in_proj.filter(models.File.subpath.like(f"{x.rstrip(os.sep)}%"))
                        .with_entities(
                            models.File.name,
                            models.File.name_in_bucket,
                            models.File.subpath,
                            models.File.size_original,
                            models.File.size_stored,
                            models.File.salt,
                            models.File.public_key,
                            models.File.checksum,
                            models.File.compressed,
                        )
                        .all()
                    )

                    if list_of_files:
                        files_in_folders[x] = [tuple(x) for x in list_of_files]

        except sqlalchemy.exc.SQLAlchemyError as err:
            return flask.make_response(str(err), 500)
        else:

            # Make dict for files with info
            files_single = {
                x[0]: {
                    "name_in_bucket": x[1],
                    "subpath": x[2],
                    "size_original": x[3],
                    "size_stored": x[4],
                    "key_salt": x[5],
                    "public_key": x[6],
                    "checksum": x[7],
                    "compressed": x[8],
                }
                for x in files
            }

        try:
            return flask.jsonify({"files": files_single, "folders": files_in_folders})
        except Exception as err:
            flask.current_app.logger.exception(str(err))


class FileInfoAll(flask_restful.Resource):
    """Get info on all project files."""

    @auth.login_required
    def get(self):
        """Get file info."""

        project = marshmallows.ProjectRequiredSchema().load(flask.request.args)

        files = {}
        try:
            all_files = (
                models.File.query.filter_by(project_id=project.id)
                .with_entities(
                    models.File.name,
                    models.File.name_in_bucket,
                    models.File.subpath,
                    models.File.size_original,
                    models.File.size_stored,
                    models.File.salt,
                    models.File.public_key,
                    models.File.checksum,
                    models.File.compressed,
                )
                .all()
            )
        except sqlalchemy.exc.SQLAlchemyError as err:
            return flask.make_response(str(err), 500)
        else:
            if all_files is None or not all_files:
                return flask.make_response(f"The project {project.public_id} is empty.", 401)

            files = {
                x[0]: {
                    "name_in_bucket": x[1],
                    "subpath": x[2],
                    "size_original": x[3],
                    "size_stored": x[4],
                    "key_salt": x[5],
                    "public_key": x[6],
                    "checksum": x[7],
                    "compressed": x[8],
                }
                for x in all_files
            }

        return flask.jsonify({"files": files})


class UpdateFile(flask_restful.Resource):
    """Update file info after download"""

    @auth.login_required
    def put(self):
        """Update info in db."""

        project = marshmallows.ProjectRequiredSchema().load(flask.request.args)

        # Get file name from request from CLI
        file_name = flask.request.json.get("name")
        if not file_name:
            return flask.make_response("No file name specified. Cannot update file.", 500)

        # Update file info
        try:
            flask.current_app.logger.debug(
                "Updating file in current project: %s", project.public_id
            )

            flask.current_app.logger.debug(f"File name: {file_name}")
            file = models.File.query.filter(
                sqlalchemy.and_(
                    models.File.project_id == func.binary(project.id),
                    models.File.name == func.binary(file_name),
                )
            ).first()

            if not file:
                return flask.make_response(f"No such file.", 500)

            file.time_latest_download = dds_web.utils.current_time()
        except sqlalchemy.exc.SQLAlchemyError as err:
            db.session.rollback()
            flask.current_app.logger.exception(str(err))
            return flask.make_response("Update of file info failed.", 500)
        else:
            # flask.current_app.logger.debug("File %s updated", file_name)
            db.session.commit()

        return flask.jsonify({"message": "File info updated."})
