#############################
## Build main API container
#############################

# Set official image -- parent image
FROM python:3.12-alpine as base

ARG USERNAME=dds-user
ARG USER_UID=1001
ARG GROUPNAME=$USERNAME
ARG USER_GID=$USER_UID

# Create the user
RUN addgroup -g $USER_GID $GROUPNAME \
    && adduser -D -u $USER_UID -G $GROUPNAME $USERNAME

# Update and upgrade
RUN apk update && apk upgrade

# Install required dependencies...
# ...Some for build
RUN apk add g++ gcc musl-dev libffi-dev

# ...Some for requirements
RUN apk add jpeg-dev zlib-dev libjpeg

# Set time zone
RUN apk add tzdata
ENV TZ="UCT"

# Extract version from Github during build
ARG version
ENV DDS_VERSION=$version

# Copy the content to a code folder in container
COPY ./requirements.txt /code/requirements.txt

# Install all dependencies
RUN pip3 install -r /code/requirements.txt

# Copy the content to a code folder in container - The owner is the dds user created
COPY --chown=$USER_UID:$USER_GID . /code

# Add code directory in pythonpath
ENV PYTHONPATH /code

###################
## TEST CONTAINER
###################
FROM base as test
RUN pip3 install -r /code/tests/requirements-test.txt

# The version of mariadb-client should match the version of the mariadb server
# Because of how alpine works, this is how to pin a version. However, it can break if this branch is removed from alpine
# https://superuser.com/questions/1055060/how-to-install-a-specific-package-version-in-alpine
# https://pkgs.alpinelinux.org/packages?name=mariadb-client&branch=v3.19&repo=&arch=x86_64&origin=&flagged=&maintainer=
RUN apk add mariadb-client=~10.11 --repository https://dl-cdn.alpinelinux.org/alpine/v3.19/main/

# Switch to the user
USER $USERNAME

###################
## BUILD FRONTEND
###################
FROM node:18 as nodebuilder
COPY ./dds_web/static /build
WORKDIR /build
RUN npm install -g npm@10.9.2 --quiet
RUN npm install --quiet
RUN npm run css

#########################
## PRODUCTION CONTAINER
#########################
FROM base as production

RUN pip install gunicorn eventlet

# Add parameters for gunicorn
ENV GUNICORN_CMD_ARGS "--bind=0.0.0.0:5000 --workers=10 --worker-class=eventlet --timeout 120 --forwarded-allow-ips='*' --access-logfile - --error-logfile -"

# Set working directory - 'code' dir in container, 'code' dir locally (in code)
WORKDIR /code/dds_web

# Get the built frontend
COPY --from=nodebuilder /build ./static

# Switch to the user
USER $USERNAME

# Run app -- needs to be in WORKDIR
CMD ["gunicorn", "run_app:app_obj"]
