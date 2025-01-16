# Data Delivery System Web / API: Changelog

Please add a _short_ line describing the PR you make, if the PR implements a specific feature or functionality, or refactor. Not needed if you add very small and unnoticable changes. Not needed when PR includes _only_ tests for already existing feature.

## 2022-02-09 - 2022-02-23

- Secure operations that require cryptographic keys are protected for each user with the user's password ([#889](https://github.com/ScilifelabDataCentre/dds_web/pull/889))
- Implemented the functionality to add project to the invites of a new user as outlined in [issue 887](https://github.com/scilifelabdatacentre/dds_web/issues/887) ([PR888](https://github.com/ScilifelabDataCentre/dds_web/pull/888)).
- Create endpoint for renewing users project access, e.g. after password reset ([886](https://github.com/ScilifelabDataCentre/dds_web/pull/885))
- Added tests for web login and change password ([900](https://github.com/ScilifelabDataCentre/dds_web/pull/900))
- Size-based log rotation working (15\*1MiB)[#897](https://github.com/ScilifelabDataCentre/dds_web/pull/897))
- Added check for project status in RemoveContents endpoint as outlined in [issue 898](https://github.com/ScilifelabDataCentre/dds_web/issues/898) ([PR899](https://github.com/ScilifelabDataCentre/dds_web/pull/899)).
- Implemented the functionality to add project to the invites of a new user as outlined in [issue 887](https://github.com/scilifelabdatacentre/dds_web/issues/887) ([PR888](https://github.com/ScilifelabDataCentre/dds_web/pull/888)).
- Changed and fixed the implementation of password reset ([#891](https://github.com/ScilifelabDataCentre/dds_web/pull/891)
- Changed log rotation to standard format and set maximum to 1MiB per file, max 15 files ([897](https://github.com/ScilifelabDataCentre/dds_web/pull/897))
- Add functionality for reactivating project access for user ([886](https://github.com/ScilifelabDataCentre/dds_web/pull/886))
- Check if user is active before allowing password reset ([903](https://github.com/ScilifelabDataCentre/dds_web/pull/903))
- Add support for database migrations using flask-migrate/Alembic ([#890](https://github.com/ScilifelabDataCentre/dds_web/pull/890))
- Invite Researchers to projects ([911](https://github.com/ScilifelabDataCentre/dds_web/pull/911))
- Changed `is_sensitive` to `non_sensitive` and set to default False ([#913](https://github.com/ScilifelabDataCentre/dds_web/pull/913))
- Rearrangement and clean up of the token ([910](https://github.com/ScilifelabDataCentre/dds_web/pull/910))

## 2022-02-23 - 2022-03-09

- Add landing page after password reset ([#931](https://github.com/ScilifelabDataCentre/dds_web/pull/931))
- Add endpoint for health check (intended for readinessProbe) ([#933](https://github.com/ScilifelabDataCentre/dds_web/pull/933))
- Introduced a `--no-mail` flag in the CLI respectively a `send_email: True/False` json parameter to fix [#924](https://github.com/scilifelabdatacentre/dds_web/issues/924) ([#926](https://github.com/ScilifelabDataCentre/dds_web/pull/926))
- Invite Unit Admin (temporary way) ([#938](https://github.com/ScilifelabDataCentre/dds_web/pull/938))
- Add support for getting IPs from X-Forwarded-For ([#952](https://github.com/ScilifelabDataCentre/dds_web/pull/952))
- Relax requirements for usernames (wider length range, `.` and `-`) ([#943](https://github.com/ScilifelabDataCentre/dds_web/pull/943))
- Delay committing project to db until after the bucket has been created ([#967](https://github.com/ScilifelabDataCentre/dds_web/pull/967))
- Fix logic for notification about sent email ([#963](https://github.com/ScilifelabDataCentre/dds_web/pull/963))
- Extended the `dds_web.api.dds_decorators.logging_bind_request` decorator to catch all not yet caught exceptions and make sure they will be logged ([#958](https://github.com/ScilifelabDataCentre/dds_web/pull/958)).
- Increase the security of the session cookie using HTTPONLY and SECURE ([#972](https://github.com/ScilifelabDataCentre/dds_web/pull/972))
- Add role when listing project users ([#974](https://github.com/ScilifelabDataCentre/dds_web/pull/974))
- Add custom error messages to registration form ([#975](https://github.com/ScilifelabDataCentre/dds_web/pull/975))
- Fix format of self deletion email ([#984](https://github.com/ScilifelabDataCentre/dds_web/pull/984))
- Add a full zero-conf development environment ([#993](https://github.com/ScilifelabDataCentre/dds_web/pull/993))
- Include frontend build in the backend production target ([#1011](https://github.com/ScilifelabDataCentre/dds_web/pull/1011))
- Correct response about project being created when email validation fails for users ([#1014](https://github.com/ScilifelabDataCentre/dds_web/pull/1014))
- Introduced an additional validator `dds_web.utils.contains_disallowed_characters` to fix issue [#1007](https://github.com/scilifelabdatacentre/dds_web/issues/1007) ([#1021](https://github.com/ScilifelabDataCentre/dds_web/pull/1021)).
- Fix regex for listing and deleting files [#1029](https://github.com/scilifelabdatacentre/dds_web/issues/1029)
- Hides the "Size" and "total_size" variables according to the role and project status ([#1032](https://github.com/ScilifelabDataCentre/dds_web/pull/1032)).

## 2022-03-09 - 2022-03-23

- Introduce a separate error message if someone tried to add an unit user to projects individually. ([#1039](https://github.com/ScilifelabDataCentre/dds_web/pull/1039))
- Catch KeyNotFoundError when user tries to give access to a project they themselves do not have access to ([#1045](https://github.com/ScilifelabDataCentre/dds_web/pull/1045))
- Display an error message when the user makes too many authentication requests. ([#1034](https://github.com/ScilifelabDataCentre/dds_web/pull/1034))
- When listing the projects, return whether or not the user has a project key for that particular project ([#1049](https://github.com/ScilifelabDataCentre/dds_web/pull/1049))
- New endpoint for Unit Personnel and Admins to list the other Unit Personnel / Admins within their project ([#1050](https://github.com/ScilifelabDataCentre/dds_web/pull/1050))
- Make previous HOTP invalid at password reset ([#1054](https://github.com/ScilifelabDataCentre/dds_web/pull/1054))
- New PasswordReset table to keep track of when a user has requested a password reset ([#1058](https://github.com/ScilifelabDataCentre/dds_web/pull/1058))
- New endpoint for listing Units as Super Admin ([1060](https://github.com/ScilifelabDataCentre/dds_web/pull/1060))
- New endpoint for listing unit users as Super Admin ([#1059](https://github.com/ScilifelabDataCentre/dds_web/pull/1059))
- Future-proofing the migrations ([#1040](https://github.com/ScilifelabDataCentre/dds_web/pull/1040))
- Return int instead of string from files listing and only return usage info if right role ([#1070](https://github.com/ScilifelabDataCentre/dds_web/pull/1070))
- Batch deletion of files (breaking atomicity) ([#1067](https://github.com/ScilifelabDataCentre/dds_web/pull/1067))
- Change token expiration time to 7 days (168 hours) ([#1061](https://github.com/ScilifelabDataCentre/dds_web/pull/1061))
- Add possibility of deleting invites (temporary fix in delete user endpoint) ([#1075](https://github.com/ScilifelabDataCentre/dds_web/pull/1075))
- Flask command `create-unit` to create unit without having to interact with database directly ([#1075](https://github.com/ScilifelabDataCentre/dds_web/pull/1075))
- Let project description include . and , ([#1080](https://github.com/ScilifelabDataCentre/dds_web/pull/1080))
- Catch OperationalError if there is a database malfunction in `files.py` ([#1089](https://github.com/ScilifelabDataCentre/dds_web/pull/1089))
- Switched the validation for the principal investigator from string to email ([#1084](https://github.com/ScilifelabDataCentre/dds_web/pull/1084)).

## 2022-03-23 - 2022-04-06

- Add link in navbar to the installation documentation ([#1112](https://github.com/ScilifelabDataCentre/dds_web/pull/1112))
- Change from apscheduler to flask-apscheduler - solves the app context issue ([#1109](https://github.com/ScilifelabDataCentre/dds_web/pull/1109))
- Send an email to all Unit Admins when a Unit Admin has reset their password ([#1110](https://github.com/ScilifelabDataCentre/dds_web/pull/1110)).
- Patch: Add check for unanswered invite when creating project and adding user who is already invited ([#1117](https://github.com/ScilifelabDataCentre/dds_web/pull/1117))
- Cronjob: Scheduled task for changing project status from Available to Expired ([#1116](https://github.com/ScilifelabDataCentre/dds_web/pull/1116))
- Cronjob: Scheduled task for changing project status from Expired to Archived ([#1115](https://github.com/ScilifelabDataCentre/dds_web/pull/1115))
- Add a Flask command for finding and deleting "lost files" (files that exist only in db or s3) ([#1124](https://github.com/ScilifelabDataCentre/dds_web/pull/1124))

## 2022-04-06 - 2022-04-20

- New endpoint for adding a message of the day to the database ([#1136](https://github.com/ScilifelabDataCentre/dds_web/pull/1136))
- Patch: Custom error for PI email validation ([#1146](https://github.com/ScilifelabDataCentre/dds_web/pull/1146))
- New Data Delivery System logo ([#1148](https://github.com/ScilifelabDataCentre/dds_web/pull/1148))
- Cronjob: Scheduled task for deleting unanswered invites after a week ([#1147](https://github.com/ScilifelabDataCentre/dds_web/pull/1147))
- Checkbox in registration form and policy to agree to ([#1151](https://github.com/ScilifelabDataCentre/dds_web/pull/1151))
- Patch: Add checks for valid public_id when creating new unit to avoid bucket name errors ([#1154](https://github.com/ScilifelabDataCentre/dds_web/pull/1154))

## 2022-04-20 - 2022-05-04

- Renamed `api/units.py` to `api/superadmin_only.py` to reflect that it's only Super Admin accessible resources ([#1159](https://github.com/ScilifelabDataCentre/dds_web/pull/1159))
- Add unit tests for the "set_available_to_expired" and "set_expired_to_archived" functions ([#1158](https://github.com/ScilifelabDataCentre/dds_web/pull/1158))
- DC Branding: SciLifeLab logo + "Data Delivery System" in nav bar & DC branding in footer ([#1160](https://github.com/ScilifelabDataCentre/dds_web/pull/1160))

## 2022-05-04 - 2022-05-18

- `adr-tools` to document architecture decisions ([#1161](https://github.com/ScilifelabDataCentre/dds_web/pull/1161))
- Bug: API returning float again and CLI `--size` flag works again ([#1162](https://github.com/ScilifelabDataCentre/dds_web/pull/1162))
- Bug: Check for timestamp `0000-00-00 00:00:00` added and invite deleted ([#1163](https://github.com/ScilifelabDataCentre/dds_web/pull/1163))
- Add documentation of status codes in `api/project.py` ([#1164](https://github.com/ScilifelabDataCentre/dds_web/pull/1164))
- Add ability to switch to using TOTP and back to HOTP for MFA ([#936](https://github.com/scilifelabdatacentre/dds_web/issues/936))
- Patch: Fix the warning in web for too soon TOTP login (within 90 seconds) ([#1173](https://github.com/ScilifelabDataCentre/dds_web/pull/1173))
- Bug: Do not remove the bucket when emptying the project ([#1172](https://github.com/ScilifelabDataCentre/dds_web/pull/1172))
- New `add-missing-buckets` argument option to the `lost-files` flask command ([#1174](https://github.com/ScilifelabDataCentre/dds_web/pull/1174))
- Bug: Corrected `lost-files` logic and message ([#1176](https://github.com/ScilifelabDataCentre/dds_web/pull/1176))

## 2022-05-18 - 2022-06-01

- Allow all characters but unicode (e.g. emojis) in project description ([#1178](https://github.com/ScilifelabDataCentre/dds_web/pull/1178))
- Cronjob: Scheduled task for monthly usage data ([#1181](https://github.com/ScilifelabDataCentre/dds_web/pull/1181))
- New tests for `dds_web/__init__.py` ([#1185](https://github.com/ScilifelabDataCentre/dds_web/pull/1185))
- New tests for `dds_web/utils.py` ([#1188](https://github.com/ScilifelabDataCentre/dds_web/pull/1188))
- Removed FontAwesome from web ([#1192](https://github.com/ScilifelabDataCentre/dds_web/pull/1192))

## 2022-06-01 - 2022-06-15

- Change FontAwesome source link to own license ([#1194](https://github.com/ScilifelabDataCentre/dds_web/pull/1194))
- Display MOTD on web ([#1196](https://github.com/ScilifelabDataCentre/dds_web/pull/1196))

## 2022-06-15 - 2022-06-29

- Get MOTD from API ([#1198](https://github.com/ScilifelabDataCentre/dds_web/pull/1198))
- New endpoint for listing all users ([#1204](https://github.com/ScilifelabDataCentre/dds_web/pull/1204))
- Only print warning about missing bucket if the project is active ([#1203](https://github.com/ScilifelabDataCentre/dds_web/pull/1203))
- Removed version check ([#1206](https://github.com/ScilifelabDataCentre/dds_web/pull/1206))

## Summer 2022

- Do not send one time code to email if the email 2fa is getting activated ([#1236](https://github.com/ScilifelabDataCentre/dds_web/pull/1236))
- Raise AccessDeniedError with message when token specified but user not existent ([#1235](https://github.com/ScilifelabDataCentre/dds_web/pull/1235))
- Display multiple MOTDS ([#1212](https://github.com/ScilifelabDataCentre/dds_web/pull/1212))

## 2022-08-18 - 2022-09-02

- Allow Super Admins to deactivate user 2FA via authenticator app ([#1247](https://github.com/ScilifelabDataCentre/dds_web/pull/1247))
- Get troubleshooting document from Confluence ([#1244](https://github.com/ScilifelabDataCentre/dds_web/pull/1244))
- Quarterly cron job calculating projects storage usage based on the database ([#1246](https://github.com/ScilifelabDataCentre/dds_web/pull/1246))
- Add Technical Overview page with links to Confluence and to a PDF download ([#1250](https://github.com/ScilifelabDataCentre/dds_web/pull/1250))
- Technical Overview moved to repository ([#1250](https://github.com/ScilifelabDataCentre/dds_web/pull/1253))
- Troubleshooting document moved to repository and buttons added to web to link and download ([#1255](https://github.com/ScilifelabDataCentre/dds_web/pull/1255))

## 2022-09-02 - 2022-09-16

- Add storage usage information in the Units listing table for Super Admin ([#1264](https://github.com/ScilifelabDataCentre/dds_web/pull/1264))
- New endpoint for setting project as busy / not busy ([#1266](https://github.com/ScilifelabDataCentre/dds_web/pull/1266))
- Check for if project busy before status change ([#1266](https://github.com/ScilifelabDataCentre/dds_web/pull/1266))
- Bug fix: Default timestamps fixed ([#1271](https://github.com/ScilifelabDataCentre/dds_web/pull/1271))
- Change docker image to alpine ([#1272](https://github.com/ScilifelabDataCentre/dds_web/pull/1272))
- Added trivy when publishing to dockerhub ([#1276](https://github.com/ScilifelabDataCentre/dds_web/pull/1276))
- Bug fix: Cost value displayed by the --usage flag fixed ([#1274](https://github.com/ScilifelabDataCentre/dds_web/pull/1274))

## 2022-09-16 - 2022-09-30

- New endpoint: SendMOTD - send important information to users ([#1283](https://github.com/ScilifelabDataCentre/dds_web/pull/1283))
- New table: `Maintenance`, for keeping track of DDS maintenance mode ([#1284](https://github.com/ScilifelabDataCentre/dds_web/pull/1284))
- New endpoint: SetMaintenance - set maintenance mode to on or off ([#1286](https://github.com/ScilifelabDataCentre/dds_web/pull/1286))
- New endpoint: AnyProjectsBusy - check if any projects are busy in DDS ([#1288](https://github.com/ScilifelabDataCentre/dds_web/pull/1288))

## 2022-09-30 - 2022-10-14

- Bug fix: Fix the Invite.projects database model ([#1290](https://github.com/ScilifelabDataCentre/dds_web/pull/1290))
- New endpoint: ListInvites - list invites ([#1294](https://github.com/ScilifelabDataCentre/dds_web/pull/1294))

## 2022-10-14 - 2022-10-28

- Limit projects listing to active projects only; a `--show-all` flag can be used for listing all projects, active and inactive ([#1302](https://github.com/ScilifelabDataCentre/dds_web/pull/1302))
- Return name of project creator from UserProjects ([#1303](https://github.com/ScilifelabDataCentre/dds_web/pull/1303))
- Add version to the footer of the web pages ([#1304](https://github.com/ScilifelabDataCentre/dds_web/pull/1304))
- Add link to the dds instance to the end of all emails ([#1305](https://github.com/ScilifelabDataCentre/dds_web/pull/1305))
- Troubleshooting steps added to web page ([#1309](https://github.com/ScilifelabDataCentre/dds_web/pull/1309))
- Bug: Return instead of project creator if user has been deleted ([#1311](https://github.com/ScilifelabDataCentre/dds_web/pull/1311))
- New endpoint: ProjectInfo - display project information ([#1310](https://github.com/ScilifelabDataCentre/dds_web/pull/1310))

## 2022-11-11 - 2022-11-25

- Link to "How do I get my user account?" from the login form ([#1318](https://github.com/ScilifelabDataCentre/dds_web/pull/1318))

## 2022-11-25 - 2022-12-09

- Changed support email ([#1324](https://github.com/ScilifelabDataCentre/dds_web/pull/1324))
- Allow Super Admin login during maintenance ([#1333](https://github.com/ScilifelabDataCentre/dds_web/pull/1333))

## 2022-12-09 - 2023-01-09: Longer sprint due to Christmas

- Dependency: Bump `certifi` due to CVE-2022-23491 ([#1337](https://github.com/ScilifelabDataCentre/dds_web/pull/1337))
- Dependency: Bump `jwcrypto` due to CVE-2022-3102 ([#1339](https://github.com/ScilifelabDataCentre/dds_web/pull/1339))
- Cronjob: Get number of units and users for reporting ([#1324](https://github.com/ScilifelabDataCentre/dds_web/pull/1335))
- Add ability to change project information via ProjectInfo endpoint ([#1331](https://github.com/ScilifelabDataCentre/dds_web/pull/1331))
- Fix the reporting file path ([1345](https://github.com/ScilifelabDataCentre/dds_web/pull/1345))

## 2023-01-09 - 2023-01-20

- Refactoring: Move flask commands to own module `commands.py` ([#1351](https://github.com/ScilifelabDataCentre/dds_web/pull/1351))
- Workflow: Scan with Snyk on PR and schedule ([#1349](https://github.com/ScilifelabDataCentre/dds_web/pull/1349))
- Flask command (cronjob): Monitor unit usage and warn if above level ([#1350](https://github.com/ScilifelabDataCentre/dds_web/pull/1350))

## 2023-01-20 - 2023-02-03

- Workflow: Do not publish to DockerHub anymore ([#1357](https://github.com/ScilifelabDataCentre/dds_web/pull/1357))
- Refactoring: move cronjobs previously handled by APScheduler to flask commands ([#1355](https://github.com/ScilifelabDataCentre/dds_web/pull/1355))
- Bug: Fix type issue in 0c9c237cced5 (latest) migration ([#1360](https://github.com/ScilifelabDataCentre/dds_web/pull/1360))
- Database: New `Reporting` table for saving unit / user stats every month ([#1363](https://github.com/ScilifelabDataCentre/dds_web/pull/1363))
- Version bump: 2.2.6 ([#1375](https://github.com/ScilifelabDataCentre/dds_web/pull/1375))
- Workflow: Add option to publish dev image manually ([#1376](https://github.com/ScilifelabDataCentre/dds_web/pull/1376))
- Bug: Add value to `Unit.warning_level` for existing units ([#1378](https://github.com/ScilifelabDataCentre/dds_web/pull/1379))
- Workflow: Add option to run trivy on dev and master branches manually ([#1380](https://github.com/ScilifelabDataCentre/dds_web/pull/1380))

## 2023-02-03 - 2023-02-17

- Workflow: Scan with yamllint ([#1385](https://github.com/ScilifelabDataCentre/dds_web/pull/1385))

## 2023-02-17 - 2023-03-03

- Move Rotating log file maximum size and backup count to config variables ([#1388](https://github.com/ScilifelabDataCentre/dds_web/pull/1388))
- Workflow: Scan branch with trivy ([#1377](https://github.com/ScilifelabDataCentre/dds_web/pull/1377))
- Dependencies bumped ([#1387](https://github.com/ScilifelabDataCentre/dds_web/pull/1387))
  - Werkzeug: 2.0.3 --> 2.2.3 (CVE-2023-25577)
  - MarkupSafe: 2.0.1 --> 2.1.1 (prior bumps)
  - Flask-Login: 0.5.0 --> 0.6.2 (prior bumps)
  - Flask: 2.0.2 --> 2.0.3 (prior bumps)
  - Cryptography: 36.0.1 --> 39.0.1 (CVE-2023-0286)
- Npm vulnerability fixed: CVE-2022-25881 ([#1390](https://github.com/ScilifelabDataCentre/dds_web/pull/1390))
- Logging: Configure action-logging to wrap json with parent key "action" ([https://github.com/ScilifelabDataCentre/dds_web/pull/1393](https://github.com/ScilifelabDataCentre/dds_web/pull/1393))
- Workflow: Schedule trivy scan for both dev images and latest release ([#1392](https://github.com/ScilifelabDataCentre/dds_web/pull/1392))
- Improve logging of delete-invites flask command ([#1386](https://github.com/ScilifelabDataCentre/dds_web/pull/1386))
- Workflow: Schedule trivy scan for dev and latest separately ([#1395](https://github.com/ScilifelabDataCentre/dds_web/pull/1395))

# 2023-03-03 - 2023-03-17

- PR template restructured ([#1403](https://github.com/ScilifelabDataCentre/dds_web/pull/1403))
- Only allow latin1-encodable usernames and passwords ([#1402](https://github.com/ScilifelabDataCentre/dds_web/pull/1402))
- Bug: Corrected calculation of used storage space in `monitor_usage` command ([#1404](https://github.com/ScilifelabDataCentre/dds_web/pull/1404))
- Config: Define Argon2 settings in `config.py` and use same settings (as default) during password-hashing as in key-derivation for private key access ([#1406](https://github.com/ScilifelabDataCentre/dds_web/pull/1406))
- Bug: Display same message during password reset independent on if the email address is registered to an account or not ([#1408](https://github.com/ScilifelabDataCentre/dds_web/pull/1408))

# 2023-03-17 - 2023-03-31

_Nothing merged during this sprint_

# 2023-03-31 - 2023-04-14

_Nothing merged during this sprint_

# 2023-04-14 - 2023-04-28

- Documentation: Minor update of Technical Overview ([#1411](https://github.com/ScilifelabDataCentre/dds_web/pull/1411))
- Documentation: Account roles and their permissions ([#1412](https://github.com/ScilifelabDataCentre/dds_web/pull/1412))

# 2023-05-26 - 2023-06-09

- Command:
  - Save number of Unit Personnel instead of total number of unit users ([#1417](https://github.com/ScilifelabDataCentre/dds_web/pull/1417))
  - Save total number of projects ([#1418](https://github.com/ScilifelabDataCentre/dds_web/pull/1418))
  - Save number of Unit Admins ([#1419](https://github.com/ScilifelabDataCentre/dds_web/pull/1419))
  - Save number of active projects ([#1423](https://github.com/ScilifelabDataCentre/dds_web/pull/1423))
  - Change `researchuser_count` column name to `researcher_count` in Reporting table ([#1420](https://github.com/ScilifelabDataCentre/dds_web/pull/1420))
  - Save number of inactive projects ([#1426](https://github.com/ScilifelabDataCentre/dds_web/pull/1426))
  - Save number of unique Project Owners ([#1421](https://github.com/ScilifelabDataCentre/dds_web/pull/1421))
  - Save amount of TB's currently stored in system ([#1424](https://github.com/ScilifelabDataCentre/dds_web/pull/1424))
  - Save amount of TB's uploaded since start ([#1430](https://github.com/ScilifelabDataCentre/dds_web/pull/1430))
  - Save number of TBHours stored in the last month ([#1431](https://github.com/ScilifelabDataCentre/dds_web/pull/1431))
  - Save number of TBHours stored in since start ([#1434](https://github.com/ScilifelabDataCentre/dds_web/pull/1434))
- New version: 2.3.0 ([#1433](https://github.com/ScilifelabDataCentre/dds_web/pull/1433))
- Dependency: Bump `requests` to 2.31.0 due to security vulnerability alert ([#1427](https://github.com/ScilifelabDataCentre/dds_web/pull/1427))
- Endpoint: Statistics; Return all rows stored in the Reporting table ([#1435](https://github.com/ScilifelabDataCentre/dds_web/pull/1435))

# 2023-06-09 - 2023-06-23

- Dependency: Bump `Flask` to 2.2.5 due to security vulnerability alert(s) ([#1425](https://github.com/ScilifelabDataCentre/dds_web/pull/1425))
- Dependency: Bump `redis-py` to 4.5.5 due to security vulnerability alert(s) ([#1437](https://github.com/ScilifelabDataCentre/dds_web/pull/1437))
- Change from personal name to unit name if / where it's displayed in emails ([#1439](https://github.com/ScilifelabDataCentre/dds_web/pull/1439))
- Refactoring: `lost_files_s3_db` flask command changed to group with subcommands ([#1438](https://github.com/ScilifelabDataCentre/dds_web/pull/1438))

# 2023-06-26 - 2023-08-04 (Summer)

- Change display project info depending on the user role ([#1440](https://github.com/ScilifelabDataCentre/dds_web/pull/1440))
- New version: 2.4.0 ([#1443](https://github.com/ScilifelabDataCentre/dds_web/pull/1443))
- Bug fix: Web UI project listing fix ([#1445](https://github.com/ScilifelabDataCentre/dds_web/pull/1445))
- Documentation: Technical Overview, section Creating a Unit in the DDS ([#1449](https://github.com/ScilifelabDataCentre/dds_web/pull/1449))

# 2023-08-07 - 2023-08-18

- Empty endpoint: `ProjectBusy` ([#1446](https://github.com/ScilifelabDataCentre/dds_web/pull/1446))

# 2023-08-04 - 2023-08-18

- Rename storage-related columns in `Unit` table ([#1447](https://github.com/ScilifelabDataCentre/dds_web/pull/1447))
- Dependency: Bump `cryptography` to 41.0.3 due to security vulnerability alerts(s) ([#1451](https://github.com/ScilifelabDataCentre/dds_web/pull/1451))
- Allow for change of storage location ([#1448](https://github.com/ScilifelabDataCentre/dds_web/pull/1448))
- Endpoint: `UnitUserEmails`; Return primary emails for Unit Personnel- and Admins ([#1454](https://github.com/ScilifelabDataCentre/dds_web/pull/1454))
- Change message about project being busy with upload etc ([#1450](https://github.com/ScilifelabDataCentre/dds_web/pull/1450))

# 2023-08-21 - 2023-09-01

- Dependency: Bump `certifi` to 2023.07.22 due to security vulnerability alert(s) ([#1452](https://github.com/ScilifelabDataCentre/dds_web/pull/1452))
- New version: 2.5.0 ([#1458](https://github.com/ScilifelabDataCentre/dds_web/pull/1458))
- Added check for Maintenance mode status in MaintenanceMode endpoint ([#1459](https://github.com/ScilifelabDataCentre/dds_web/pull/1459))

# 2023-09-04 - 2023-09-15

- Bug fix: Database rollback added on project creation failure ([#1461](https://github.com/ScilifelabDataCentre/dds_web/pull/1461))
- Only return date (not time) from `Statistics` endpoint ([#1456](https://github.com/ScilifelabDataCentre/dds_web/pull/1456))
- Set `sto2*` columns in `Unit` table to nullable ([#1456](https://github.com/ScilifelabDataCentre/dds_web/pull/1462))
- Dependency: Bump `MariaDB` to LTS version 10.11.5 ([#1465](https://github.com/ScilifelabDataCentre/dds_web/pull/1465))
- Bug fixed: Row in `ProjectUsers` should also be added if it doesn't exist when giving Researcher access to a specific project ([#1464](https://github.com/ScilifelabDataCentre/dds_web/pull/1464))
- Workflow: Update PR template and clarify sections ([#1467](https://github.com/ScilifelabDataCentre/dds_web/pull/1467))

# 2023-09-18 - 2023-09-29

- Column `sto4_start_time` is automatically set when the create-unit command is run ([#1469](https://github.com/ScilifelabDataCentre/dds_web/pull/1469))
- Replace expired invites when there's a new invitation attempt ([#1466](https://github.com/ScilifelabDataCentre/dds_web/pull/1466))
- New version: 2.5.1 ([#1471](https://github.com/ScilifelabDataCentre/dds_web/pull/1471))
- Revoke project access for unaccepted invites ([#1468](https://github.com/ScilifelabDataCentre/dds_web/pull/1468))

# 2023-10-02 - 2023-10-13

- Project title displayed along with the internal project ID email sent when a project is released ([#1475](https://github.com/ScilifelabDataCentre/dds_web/pull/1475))
- Use full DDS name in MOTD email subject ([#1477](https://github.com/ScilifelabDataCentre/dds_web/pull/1477))
- Add flag --verify-checksum to the comand in email template ([#1478])(https://github.com/ScilifelabDataCentre/dds_web/pull/1478)
- Improved email layout; Highlighted information and commands when project is released ([#1479])(https://github.com/ScilifelabDataCentre/dds_web/pull/1479)

# 2023-10-16 - 2023-11-03 (Longer sprint due to OKR prep and höstlov)

- Added new API endpoint ProjectStatus.patch to extend the deadline ([#1480])(https://github.com/ScilifelabDataCentre/dds_web/pull/1480)
- New version: 2.5.2 ([#1482](https://github.com/ScilifelabDataCentre/dds_web/pull/1482))
- New endpoint `AddFailedFiles` for adding failed files to database ([#1472](https://github.com/ScilifelabDataCentre/dds_web/pull/1472))
- Change the generate usage command to monthly instead of quartely, and add the command to send a usage report specifying the number of months ([#1476](https://github.com/ScilifelabDataCentre/dds_web/pull/1476))
- New ADR record regarding OKR 2024 ([#1483](https://github.com/ScilifelabDataCentre/dds_web/pull/1483))

# 2023-11-6 - 2023-11-17

- Updated Pillow package version to address vulnerabities ([#1486](https://github.com/ScilifelabDataCentre/dds_web/pull/1486))
- Updated urllib3 package version to address vulnerabities ([#1487](https://github.com/ScilifelabDataCentre/dds_web/pull/1487))
- Updated PostCss Node package to address vulnerabities ([#1489](https://github.com/ScilifelabDataCentre/dds_web/pull/1489))
- Updated Several node libraries to address vulnerabities ([#1492](https://github.com/ScilifelabDataCentre/dds_web/pull/1492))
- New version: 2.6.0 ([#1494](https://github.com/ScilifelabDataCentre/dds_web/pull/1494))

# 2023-12-4 - 2023-12-15

- Implemented swagger documentation ([#1495](https://github.com/ScilifelabDataCentre/dds_web/pull/1495))
- Patch update crypthography package to address cve ([#1496](https://github.com/ScilifelabDataCentre/dds_web/pull/1496))
- Fix listing users was not showing PO ([#1497](https://github.com/ScilifelabDataCentre/dds_web/pull/1497))
- Bug: `flask send-usage` permission issue on testing and production environment ([1499](https://github.com/ScilifelabDataCentre/dds_web/pull/1499))
- New version: 2.6.1 ([#1501](https://github.com/ScilifelabDataCentre/dds_web/pull/1501))

# 2023-12-15 - 2024-01-12

- Minor update jinja2 package to address cve ([#1503](https://github.com/ScilifelabDataCentre/dds_web/pull/1503))
- Minor update jwcrypto package to address cve ([#1504](https://github.com/ScilifelabDataCentre/dds_web/pull/1504))

# 2023-01-15 - 2024-01-25

# 2024-01-15 - 2024-01-26

- Document Superadmin endpoints ([#1507](https://github.com/ScilifelabDataCentre/dds_web/pull/1507))
- Document S3 endpoints ([#1509](https://github.com/ScilifelabDataCentre/dds_web/pull/1509))
- Document Project endpoints ([#1508](https://github.com/ScilifelabDataCentre/dds_web/pull/1508))
- Document User endpoints ([#1506](https://github.com/ScilifelabDataCentre/dds_web/pull/1506))

# 2024-01-29 - 2024-02-09

- Use of a fix version of black and linted files to 24.1.1 ([#1510](https://github.com/ScilifelabDataCentre/dds_web/pull/1510))
- Run containers as non-root in development envronment ([#1498](https://github.com/ScilifelabDataCentre/dds_web/pull/1498))

# 2024-02-12 - 2024-03-08

- Criptography update to address cve ([#1512](https://github.com/ScilifelabDataCentre/dds_web/pull/1512))
- Pillow update to address cve ([#1511](https://github.com/ScilifelabDataCentre/dds_web/pull/1511))
- New version: 2.6.2 ([#1514](https://github.com/ScilifelabDataCentre/dds_web/pull/1514))
- Changes in registration from to include user agreement ([#1515](https://github.com/ScilifelabDataCentre/dds_web/pull/1515))

# 2024-02-26 - 2024-03-08

- Add link in footer for new User Agreement and Privacy Policy ([#1516](https://github.com/ScilifelabDataCentre/dds_web/pull/1516))
- New extra release, outside maintenance window, version 2.6.3 ([#1518](https://github.com/ScilifelabDataCentre/dds_web/pull/1518))

# 2024-03-11 - 2024-03-22

- Fix the files endpoints according to the openAPI standards, providing new endpoint version that co-exists with the current one ([#1505](https://github.com/ScilifelabDataCentre/dds_web/pull/1505))
- Added email to troubleshouting webpage, with obfuscation ([#1520](https://github.com/ScilifelabDataCentre/dds_web/pull/1520))

# 2024-03-25 - 2024-04-5

- Update base image and packages to address cve in docker containers ([#1523](https://github.com/ScilifelabDataCentre/dds_web/pull/1523))

# 2024-04-8 - 2024-04-19

- New version: 2.6.4 ([#1526](https://github.com/ScilifelabDataCentre/dds_web/pull/1526))

# 2024-05-6 - 2024-05-17

- Fix the User endpoints according to OpenAPI standar ([#1524](https://github.com/ScilifelabDataCentre/dds_web/pull/1524))

# 2024-05-20 - 2024-05-31

- Update Werkzeug and related libraries to solve CVE([#1530](https://github.com/ScilifelabDataCentre/dds_web/pull/1530))
- Fix raising error when archiving project, bucket deleted but DB error ([#1524](https://github.com/ScilifelabDataCentre/dds_web/pull/1524))
- Increase the identified less covered files([#1521](https://github.com/ScilifelabDataCentre/dds_web/pull/1521))
- Parse boolean inputs correctly ([#1528](https://github.com/ScilifelabDataCentre/dds_web/pull/1528))

# 2024-06-03 - 2024-06-14

- Fix the project endpoints according to the OpenAPI standard ([#1527](https://github.com/ScilifelabDataCentre/dds_web/pull/1527))
- Fix the Superadmin endpoints according to the OpenAPI standard ([#1533](https://github.com/ScilifelabDataCentre/dds_web/pull/1533))

# 2024-06-17 - 2024-06-28

- Update pymysql to address cve ([#1534](https://github.com/ScilifelabDataCentre/dds_web/pull/1534))
- Update authlib to address cve ([#1535](https://github.com/ScilifelabDataCentre/dds_web/pull/1535))
- Update node packages to address cve ([#1536](https://github.com/ScilifelabDataCentre/dds_web/pull/1536))

# 2024-07-15 - 2024-07-26

- Move raw Technical Overview doc to repo, add page numbers ([#1539](https://github.com/ScilifelabDataCentre/dds_web/pull/1539))
- Small updates to Technical Overview contents ([#1540](https://github.com/ScilifelabDataCentre/dds_web/pull/1540))
- Build Technical Overview PDF in GitHub Actions, rename to include DDS and remove option to view on GitHub ([#1541](https://github.com/ScilifelabDataCentre/dds_web/pull/1541/))
- Fixed index out of range when listing files from root ([#1543](https://github.com/ScilifelabDataCentre/dds_web/pull/1543/))
- Update Trivy GitHub Actions ([#1545](https://github.com/ScilifelabDataCentre/dds_web/pull/1545))

# 2024-07-29 - 2024-08-09

- Move raw troubleshooting doc to repo and make small updates ([#1546](https://github.com/ScilifelabDataCentre/dds_web/pull/1546))

# 2024-08-12 - 2024-08-23

_Nothing merged during this sprint_

# 2024-08-26 - 2024-09-06

- Update certifi to remove GLOBALISSUER certicates ([#1549](https://github.com/ScilifelabDataCentre/dds_web/pull/1549))
- Add CODEOWNERS file in order to define Team Hermes as owners of all files in repository ([#708](https://github.com/ScilifelabDataCentre/dds_web/pull/708))

# 2024-09-09 - 2024-09-20

- Flask command to update unit quotas ([#1551](https://github.com/ScilifelabDataCentre/dds_web/pull/1551))
- Bump python base image to 3.12 and related libraries in both web and client([#1548](https://github.com/ScilifelabDataCentre/dds_web/pull/1548))

# 2024-09-24 - 2024-10-04

- Add option to motd command for sending to unit users only([#1552](https://github.com/ScilifelabDataCentre/dds_web/pull/1552))
- Warning_level option defaults to 0.8([#1557](https://github.com/ScilifelabDataCentre/dds_web/pull/1557))

# 2024-10-07 - 2024-10-18

- Update readme: backend image is published to GHCR, not DockerHub ([#1558](https://github.com/ScilifelabDataCentre/dds_web/pull/1558))
- Workflow bug fixed: PDFs (Technical Overview and Troubleshooting) were downloaded to incorrect directory([#1559](https://github.com/ScilifelabDataCentre/dds_web/pull/1559))
- Update trivy action and add a second mirror repository to reduce TOO MANY REQUEST issue([#1560](https://github.com/ScilifelabDataCentre/dds_web/pull/1560))
- Modify the invoicing commands to send the instance name in the emails([#1561](https://github.com/ScilifelabDataCentre/dds_web/pull/1561))
- Fix the MOTD endpoint according to post merge review([#1564](https://github.com/ScilifelabDataCentre/dds_web/pull/1564))
- New version & changelog([#1565](https://github.com/ScilifelabDataCentre/dds_web/pull/1565))

# 2024-10-21 - 2024-11-01

- Workflow: Bump GitHub checkout action to v4 ([#1556](https://github.com/ScilifelabDataCentre/dds_web/pull/1556))
- Workflow: CodeQL action version(s) bumped to v3 ([#1569](https://github.com/ScilifelabDataCentre/dds_web/pull/1569))
- Workflow: Setup-node, codecov and upload-sarif action versions bumped to v4, v4 and v3, respectively ([#1570](https://github.com/ScilifelabDataCentre/dds_web/pull/1570))

# 2024-11-04 - 2024-11-15

- Removed exception for invalid token to simplify logging and reduce unnecessary error entries ([#1572](https://github.com/ScilifelabDataCentre/dds_web/pull/1572))

# 2024-11-18 – 2024-11-29

- Logging: Add which user name reset password ([https://github.com/ScilifelabDataCentre/dds_web/pull/1574](https://github.com/ScilifelabDataCentre/dds_web/pull/1574))

# 2024-12-02 – 2024-12-13

- Change the error raised upon attempt to download data after a password reset to an AuthenticationError to avoid getting an alert ([#1571](https://github.com/ScilifelabDataCentre/dds_web/pull/1571))
- Filter out the MaintenanceModeException from the logs ([#1573](https://github.com/ScilifelabDataCentre/dds_web/pull/1573))
- Bugfix: Quick and dirty change to prevent `dds ls --tree` from failing systematically ([#1575](https://github.com/ScilifelabDataCentre/dds_web/pull/1575))
- Update backend Dockerfile to pin a fixed version of mariadb-client ([#1581](https://github.com/ScilifelabDataCentre/dds_web/pull/1581))
- Update documentation regarding 'Upload' or 'Download' added to end of delivery directory name depending on command ([#1580](https://github.com/ScilifelabDataCentre/dds_web/pull/1580))
- Modify the monitor usage command to send warning to the affected unit as well as Data Centre([#1562](https://github.com/ScilifelabDataCentre/dds_web/pull/1562))
- Run npm audit fix to solve node cve's ([#1577](https://github.com/ScilifelabDataCentre/dds_web/pull/1577)

# 2024-12-16 - 2024-12-20

- New version: 2.9.0 ([#1584](https://github.com/ScilifelabDataCentre/dds_web/pull/1584))
- Instructions regarding database migrations moved to migrations directory, and Linkspector action added to scan for incorrect links in MD ([#1576](https://github.com/ScilifelabDataCentre/dds_web/pull/1576))

# 2024-12-20 - 2025-01-17

- Make release template ([#1587](https://github.com/ScilifelabDataCentre/dds_web/pull/1587))
- Fix codecov action ([#1589](https://github.com/ScilifelabDataCentre/dds_web/pull/1589))
