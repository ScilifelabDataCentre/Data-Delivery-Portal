<p>
   <h1 align="center">Data Delivery System Web / API</h1>
</p>

<p align="center">
   <img width="70%" src="https://github.com/ScilifelabDataCentre/dds_web/blob/master/dds_web/templates/components/hero_image.svg">
</p>

<p align="center">
   <img alt="Release" src="https://img.shields.io/github/v/release/SciLifeLabDataCentre/dds_web">
   <a href="https://opensource.org/licenses/MIT">
      <img alt="Licence: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg">
   </a>
   <a href="[https://opensource.org/licenses/MIT](https://github.com/psf/black)">
      <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
   </a>
   <a href="https://prettier.io/">
      <img alt="Code style: prettier" src="https://img.shields.io/badge/code_style-prettier-ff69b4.svg">
   </a>
   <br />
   <img alt="Linting" src="https://github.com/ScilifelabDataCentre/dds_web/actions/workflows/python-black.yml/badge.svg">
   <img alt="CodeQL" src="https://github.com/ScilifelabDataCentre/dds_web/actions/workflows/codeql-analysis.yml/badge.svg">
   <a href="https://codecov.io/github/ScilifelabDataCentre/dds_web" > 
      <img src="https://codecov.io/github/ScilifelabDataCentre/dds_web/graph/badge.svg?token=r5tM6o08Sd"/> 
   </a>
   <img alt="Tests" src="https://github.com/ScilifelabDataCentre/dds_web/actions/workflows/docker-compose-tests.yml/badge.svg">
</p>
<p align="center">
   <b>Links</b>
   <br />
   <a href="https://scilifelabdatacentre.github.io/dds_cli/">
      <img alt="Documentation" src="https://img.shields.io/badge/-Documentation-222222?logo=github-pages">
   </a>
   <a href="https://github.com/ScilifelabDataCentre/dds_web/blob/master/doc/technical-overview.md">
      <img alt="Technical Overview" src="https://img.shields.io/badge/-Technical%20Overview-informational?logo=github">
   </a>
   <a href="https://github.com/ScilifelabDataCentre/dds_web/wiki/Architecture-Decision-Record,-ADR">
      <img alt="Architecture Decision Record" src="https://img.shields.io/badge/-ADR-000000?logo=github">
   </a>
   <a href="https://github.com/ScilifelabDataCentre/dds_web/blob/master/doc/troubleshooting.md">
      <img alt="Troubleshooting" src="https://img.shields.io/badge/-Troubleshooting%20Guide-red?logo=github">
   </a>
   <a href="https://github.com/ScilifelabDataCentre/dds_cli">
      <img alt="CLI" src="https://img.shields.io/badge/-CLI-yellow?logo=github">
   </a>
</p>

## About

**The Data Delivery System (DDS) is a cloud-based system for all SciLifeLab platforms where data generated throughout each project can be delivered to the research groups in a fast, secure and simple way. The Web / API is the backend, handling the requests and the logic behind the scenes.**

> _The Data Delivery System is developed and maintained by the SciLifeLab Data Centre. National Genomics Infrastructure (NGI) Stockholm has been a part of the development team during 2021 and early 2022._
>
> _This project is supported by EIT Digital, activity number 19390. This deliverable consists of design document and implementation report of application and validation of VEIL.AI technology in SciLifeLab context in Sweden._

---

## Table of Contents

- [Development Setup](#development-setup)
  - [Profiles](#profiles)
  - [Debugging inside docker](#python-debugger-inside-docker)
  - [Config settings](#config-settings)
  - [Database changes](#database-changes)
- [Production Instance](#production-instance)

## Development Setup

When developing this software, we recommend that you run the web server locally using Docker.
You can download Docker here: <https://docs.docker.com/get-docker/>

Then, fork this repository and clone to your local system.
In the root folder of the repo, run the server with one of the following profiles (_plain_, _dev_, _full-dev_, _cli_) depending on your needs.

### Profiles

#### Application & Database: Plain

```bash
docker-compose up
```

This command will orchestrate the building and running of two containers: one for the SQL database (`mariadb`) and one for the application.

#### Mailcatcher: `dev`

```bash
docker-compose --profile dev up
```

This will give you the above two containers, but also `mailcatcher` that will allow you to read
any sent emails by going to `localhost:1080` in a web browser.

#### Minio S3 Storage & Limiter: `full-dev`

```bash
docker-compose --profile full-dev up
```

Will also activate minio for s3 storage (clearly not functional with cli) and redis to enable a persistent limiter for the API.
You also need to uncomment `RATELIMIT_STORAGE_URI` in `docker-compose.yml` to enable redis.

If you prefer, you can run the web servers in 'detached' mode with the `-d` flag, which does not block your terminal.
If using this method, you can stop the web server with the command `docker-compose down`.

#### CLI development against local environment: `cli`

```bash
docker-compose --profile cli up
```

Will start database, backend, minio, and mailcatcher. Will also start an extra container prepared for working with the CLI.

Requires that dds_cli is checked out in `../dds_cli` (otherwise adapt the volume path in `docker-compose.yml`).

1. Start docker-compose with the `cli` profile
2. Inject into the `dds_cli` container:

   ```bash
   docker exec -it dds_cli /bin/sh
   ```

Then you can freely use the dds cli component against the local development setup in the active CLI.

### Python debugger inside docker

It's possible to use the interactive debugging tool `pdb` inside Docker with this method:

1. Edit the `docker-compose.yml` and for the `backend` service, add:

   ```yaml
   tty: true
   stdin_open: true
   ```

   just under

   ```yaml
   ports:
     - 127.0.0.1:5000:5000
   ```

2. Put `import pdb; pdb.set_trace()` in the python code where you would like to activate the debugger.
3. Run with docker-compose as normal.
4. Find out the id of the container running the `backend`.

   ```bash
   docker container ls
   ```

5. Attach to the running backend container:

   ```bash
   docker container attach <container_id/name>
   ```

### Config settings

When run from the cloned repo, all settings are set to default values.
These values are publicly visible on GitHub and **should not be used in production!**

> ❗️
> **At the time of writing, upload within projects created in the development database will most likely not work.**
> To use the upload functionality with the `CLI`, first create a project.

The following test usernames ship in the development setup:

- `superadmin`
- `unituser_1`
- `unituser_2`
- `researchuser_1`
- `researchuser_2`

All have the password: `password`

### Database changes

If you modify the database models (e.g. tables or indexes), you must create a migration for the changes. We use `Alembic` (via `flask-migrate`) which compares our database models with the running database to generate a suggested migration.

For instructions on how to do this, see [the README in the migrations directory](./migrations/README.md).

## Run tests

Tests run on github actions on every pull request and push against master and dev. To run the tests locally, use this command:

```bash
docker-compose -f docker-compose.yml -f tests/docker-compose-test.yml up --build --exit-code-from backend
```

This will create a test database in the mariadb container called `DeliverySystemTest` which will be populated before a test and emptied after a test has finished.

It's possible to supply arguments to pytest via the environment variable `$DDS_PYTEST_ARGS`.
For example to only run the `test_x` inside the file `tests/test_y.py` you would set this variable as follows: `export DDS_PYTEST_ARGS=tests/test_y.py::test_x`.

To run interactively, use the following command:

```bash
docker-compose -f docker-compose.yml -f tests/docker-compose-test-interactive.yml up --build --exit-code-from backend
```

Then in a new terminal, shell into the container and run pytest:

```bash
docker exec -it dds_backend /bin/sh
```

```bash
pytest
```

If you want to run tests quickly, without rebuilding the database each time, set the `SAVE_DB` environment variable:

```bash
SAVE_DB=1 pytest
```

Note that this stops the database from being deleted, so it will speed up the _next_ run.
Equally, if you want to tear down you need to run pytest _twice_ without it, as it only affects the tear down.

---

## Production Instance

The production version of the backend image is published at the [GitHub Container Registry (GHCR, ghcr.io/scilifelabdatacentre/dds-backend)](https://github.com/scilifelabdatacentre/dds_web/pkgs/container/dds-backend). It can also be built by running:

```bash
docker build --target production -f Dockerfiles/backend.Dockerfile .
```

Use `docker-compose.yml` as a reference for the required environment.

### Configuration

The environment variable `DDS_APP_CONFIG` defines the location of the config file, e.g. `/code/dds_web/dds_app.cfg`. The config values are listed in `dds_web/config.py`. Add them to the file in the format:

```python
MAX_CONTENT_LENGTH = 0x1000000
MAX_DOWNLOAD_LIMIT = 1000000000
```

> ❗ It is recommended that you redefine all values in `config.py` in your config file to avoid using default values by mistake.

### Initialise the database

Before you can use the system, you must run `flask db upgrade` to initialise the database schema and prepare for future database migrations. You can also add a superuser by running `flask init-db production`. In order to customize the user, make sure to set the `SUPERADMIN*` config options.

### Upgrades

Whenever you upgrade to a newer version, start by running `flask db upgrade` to make sure that the database schema is up-to-date.
