"""USED ONLY DURING DEVELOPMENT! Adds test data to the database."""

import os
import uuid

from flask import current_app

from dds_web import db, timestamp

from dds_web.database.models import User, Project, Facility, File, Version


def fill_db():
    """Fills the database with initial entries used for development."""

    facilities = [
        Facility(
            public_id="public_facility_id",
            name="Facility 1",
            internal_ref="fac",
            safespring=current_app.config.get("DDS_SAFE_SPRING_PROJECT"),
        )
    ]

    projects = [
        Project(
            public_id="public_project_id",
            title="project_title",
            category="Category",
            date_created=timestamp(),
            date_updated=timestamp(),
            status="Ongoing",
            description="This is a test project",
            pi="PI",
            size=7357,
            bucket=f"publicproj-{str(timestamp(ts_format='%Y%m%d%H%M%S'))}-{str(uuid.uuid4())}",
            public_key="08D0D813DD7DD2541DF58A7E5AB651D20299F741732B0DC8B297A2D4CB43626C",
            private_key="5F39E1650CC7592EF2A06FDD37FB576EFE19C1C0C4FBDF0C799EBE19FD4B731805C25213D9398B09A7F3A0CCADA71B7E",
            privkey_salt="C2BB3FB2BBBA0DD01A6A2F5937C9D84C",
            privkey_nonce="D652B8C4554B675FB780A6EE",
            facility_id=facilities[0],
        )
    ]

    users = [
        User(
            username="username",
            password="$argon2id$v=19$m=102400,t=2,p=8$0jcemW3Ln+HTPUt/E3xtKQ$aZGqrrBBU5gq5TbWYwUWD62UiQUmTksbKOkmbMJzdhs",
            role="researcher",
            permissions="-gl--",
            first_name="User",
            last_name="Name",
            facility_id=None,
        ),
        User(
            username="admin",
            password="$argon2id$v=19$m=102400,t=2,p=8$0jcemW3Ln+HTPUt/E3xtKQ$aZGqrrBBU5gq5TbWYwUWD62UiQUmTksbKOkmbMJzdhs",
            role="admin",
            permissions="a-l--",
            first_name="Ad",
            last_name="Min",
            facility_id=None,
        ),
        User(
            username="facility_admin",
            password="$argon2id$v=19$m=102400,t=2,p=8$0jcemW3Ln+HTPUt/E3xtKQ$aZGqrrBBU5gq5TbWYwUWD62UiQUmTksbKOkmbMJzdhs",
            role="facility",
            permissions="a-l--",
            first_name="Facility",
            last_name="Admin",
            facility_id=facilities[0],
        ),
        User(
            username="facility",
            password="$argon2id$v=19$m=102400,t=2,p=8$0jcemW3Ln+HTPUt/E3xtKQ$aZGqrrBBU5gq5TbWYwUWD62UiQUmTksbKOkmbMJzdhs",
            role="facility",
            permissions="--lpr",
            first_name="Faci",
            last_name="Lity",
            facility_id=facilities[0],
        ),
    ]

    files = [
        File(
            public_id="file_public_id",
            name="notafile.txt",
            name_in_bucket="testtesttest.txt",
            subpath="subpath",
            size_original=0,  # bytes
            size_stored=0,
            compressed=False,
            public_key="test",
            salt="test",
            checksum="",
            project_id=projects[0],
        )
    ]

    versions = [
        Version(
            size_stored=files[0].size_stored,
            time_uploaded=timestamp(),
            active_file=files[0],
            project_id=projects[0],
        )
    ]

    # Foreign key/relationship updates
    for p in projects:
        for u in users:
            u.projects.append(p)

    for u in users:
        if u.facility_id:
            facilities[0].users.append(u)

    for f in files:
        projects[0].files.append(f)

    for p in projects:
        facilities[0].projects.append(p)

    for v in versions:
        projects[0].file_versions.append(v)
        files[0].versions.append(v)

    db.session.add_all(facilities)
    db.session.add_all(projects)
    db.session.add_all(users)
    db.session.add_all(files)
    db.session.add_all(versions)

    # Required for change in db
    db.session.commit()
