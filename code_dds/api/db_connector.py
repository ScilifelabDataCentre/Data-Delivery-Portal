"""API DB Connector module"""

###############################################################################
# IMPORTS ########################################################### IMPORTS #
###############################################################################

# Standard library
import traceback
import os

# Installed
import flask
import sqlalchemy

# Own modules
from code_dds.db_code import models
from code_dds import db
from code_dds.api.dds_decorators import token_required
from code_dds.api.api_s3_connector import ApiS3Connector

###############################################################################
# CLASSES ########################################################### CLASSES #
###############################################################################


@token_required
class DBConnector:
    """Class for performing database actions."""

    def __init__(self, *args, **kwargs):

        try:
            self.current_user, self.project = args
        except ValueError as err:
            flask.abort(500, str(err))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False  # uncomment to pass exception through

        return True

    def get_bucket_name(self):
        """Get bucket name from database"""

        bucketname, error = (None, "")
        try:
            bucket = (
                models.Project.query.filter_by(id=self.project["id"])
                .with_entities(models.Project.bucket)
                .first()
            )
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)
        else:
            bucketname = bucket[0]

        return bucketname, error

    def filename_in_bucket(self, filename):
        """Get filename in bucket."""

        name_in_bucket, error = (None, "")
        try:
            file = models.File.query.filter_by(project_id=self.project["id"]).all()
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)
        else:
            name_in_bucket = file[0]

        return name_in_bucket, error

    def project_size(self):
        """Get size of project"""

        num_proj_files, error = (0, "")
        try:
            num_proj_files = models.File.query.filter_by(
                project_id=self.project["id"]
            ).count()
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)

        return num_proj_files, error

    def items_in_subpath(self, folder="."):
        """Get all items in root folder of project"""

        distinct_files, distinct_folders, error = ([], [], "")
        # Get everything in root:
        # Files have subpath "." and folders do not have child folders
        # Get everything in folder:
        # Files have subpath == folder and folders have child folders (regexp)
        try:
            # All files in project
            files = models.File.query.filter_by(project_id=self.project["id"])

            # File names in root
            distinct_files = (
                files.filter(models.File.subpath == folder)
                .with_entities(models.File.name, models.File.size)
                .all()
            )

            # Folder names in folder (or root)
            if folder == ".":
                # Get distinct folders in root, subpath should not be "."
                distinct_folders = (
                    files.filter(models.File.subpath != folder)
                    .with_entities(models.File.subpath)
                    .distinct()
                    .all()
                )

                # Get first subpath (may be many and first may not have files in)
                first_parts = set(x[0].split(os.sep)[0] for x in distinct_folders)
                distinct_folders = list(first_parts)
            else:
                # Get distinct sub folders in specific folder with regex
                distinct_folders = (
                    files.filter(
                        models.File.subpath.op("regexp")(f"^{folder}(\/[^\/]+)+$")
                    )
                    .with_entities(models.File.subpath)
                    .distinct()
                    .all()
                )

                # Get length of specified folder
                len_folder = len(folder.split(os.sep))

                # Get subfolders in level under specified folder
                split_paths = set(
                    f"{os.sep}".join(x[0].split(os.sep)[: len_folder + 1])
                    for x in distinct_folders
                )
                distinct_folders = list(split_paths)

        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)

        return distinct_files, distinct_folders, error

    def folder_size(self, folder_name="."):
        """Get total size of folder"""

        tot_file_size, error = (None, "")
        try:
            file_info = (
                models.File.query.with_entities(
                    sqlalchemy.func.sum(models.File.size).label("sizeSum")
                )
                .filter(
                    sqlalchemy.and_(
                        models.File.project_id == self.project["id"],
                        models.File.subpath.like(f"{folder_name}%"),
                    )
                )
                .first()
            )
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)
        else:
            tot_file_size = file_info.sizeSum

        return tot_file_size, error

    def delete_all(self):
        """Delete all files in project."""

        deleted, error = (False, "")
        try:
            num_deleted = models.File.query.filter_by(
                project_id=self.project["id"]
            ).delete()

            # TODO (ina): put in class
            # change project size
            current_project = models.Project.query.filter_by(
                id=self.project["id"]
            ).first()
            current_project.size = 0

            db.session.commit()
        except sqlalchemy.exc.SQLAlchemyError as err:
            db.session.rollback()
            error = str(err)
        else:
            if num_deleted == 0:
                error = f"There are no files within project {self.project['id']}."
                deleted = False
            else:
                deleted = True

        return deleted, error

    def delete_folder(self, folder):
        """Delete all items in folder"""

        exists, deleted, error = (False, False, "")
        try:
            # File names in root
            files = (
                models.File.query.filter_by(project_id=self.project["id"])
                .filter(
                    sqlalchemy.or_(
                        models.File.subpath == folder,
                        models.File.subpath.op("regexp")(f"^{folder}(\/[^\/]+)?$"),
                    )
                )
                .all()
            )
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)

        if files and files is not None:
            exists = True
            try:
                current_project = models.Project.query.filter_by(
                    id=self.project["id"]
                ).first()
                for x in files:
                    old_size = x.size
                    db.session.delete(x)
                    current_project.size -= old_size
                # _ = [db.session.delete(x) for x in files]
                # _ = [current_project.size - x.size for x in files]

            except sqlalchemy.exc.SQLAlchemyError as err:
                error = str(err)
            else:
                deleted = True

        return exists, deleted, error

    def delete_multiple(self, files):
        """Delete multiple files."""

        not_removed_dict, not_exist_list, error = ({}, [], "")

        with ApiS3Connector() as s3conn:
            # Error if not enough info
            if None in [s3conn.url, s3conn.keys, s3conn.bucketname]:
                return (
                    not_removed_dict,
                    not_exist_list,
                    "No s3 info returned! " + s3conn.message,
                )

            # Delete each file
            for x in files:
                # Delete from db
                in_db, delete_ok, name_in_bucket, error = self.delete_one(filename=x)

                # Non existant files cannot be deleted
                if not in_db:
                    not_exist_list.append(x)
                    continue

                # Failure to delete
                if not delete_ok or name_in_bucket is None:
                    db.session.rollback()
                    not_removed_dict[x] = error
                    continue

                # Remove from s3 bucket
                delete_ok, error = s3conn.remove_one(file=name_in_bucket)
                if not delete_ok:
                    db.session.rollback()
                    not_removed_dict[x] = error
                    continue

                # Commit to db if ok
                try:
                    db.session.commit()
                except sqlalchemy.exc.SQLAlchemyError as err:
                    db.session.rollback()
                    not_removed_dict[x] = str(err)
                    continue

        return not_removed_dict, not_exist_list, error

    def delete_one(self, filename):
        """Delete a single file in project."""

        exists, deleted, name_in_bucket, error = (False, False, None, "")

        # Get matching files in project
        try:
            file = models.File.query.filter_by(
                name=filename, project_id=self.project["id"]
            ).first()

        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)

        # Delete if found, but do not commit yet
        if file or file is not None:
            exists, name_in_bucket = (True, file.name_in_bucket)
            try:
                # TODO (ina): put in own class
                old_size = file.size
                current_project = models.Project.query.filter_by(
                    id=self.project["id"]
                ).first()
                db.session.delete(file)
                current_project.size -= old_size
            except sqlalchemy.exc.SQLAlchemyError as err:
                db.session.rollback()
                error = str(err)
            else:
                deleted = True

        return exists, deleted, name_in_bucket, error

    def delete_dir(self, foldername):
        """Delete all files in a folder"""

        exists, deleted, errors = (False, None, None)

        # Get files in folder
        try:
            files_in_folder = models.File.query.filter_by(
                project_id=self.project["id"], subpath=foldername
            ).all()
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)

        # Get bucket info and delete files
        if files_in_folder or files_in_folder is not None:
            exists, deleted, errors = (True, {}, {})

            for x in files_in_folder:
                filename = x.name
                nameinbucket = x.name_in_bucket

                try:
                    db.session.delete(x)
                except sqlalchemy.exc.SQLAlchemyError as err:
                    db.session.rollback()
                    errors[filename] = str(err)
                else:
                    deleted[filename] = {"name_in_bucket": nameinbucket}

        return exists, deleted, errors

    def cloud_project(self):
        """Get safespring project"""

        sfsp_proj, error = ("", "")
        if hasattr(self.current_user, "safespring"):
            return self.current_user.safespring, error

        try:
            proj_fac = (
                models.Project.query.filter_by(id=self.project["id"])
                .with_entities(models.Project.facility)
                .first()
            )

            print(proj_fac, flush=True)

            sfsp_proj_info = (
                models.Facility.query.filter_by(public_id=proj_fac[0])
                .with_entities(models.Facility.safespring)
                .first()
            )
        except sqlalchemy.exc.SQLAlchemyError as err:
            error = str(err)
        else:
            sfsp_proj = sfsp_proj_info[0]
            print(f"project: {sfsp_proj}", flush=True)

        return sfsp_proj, error
