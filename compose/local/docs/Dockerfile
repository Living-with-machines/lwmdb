ARG PYTHON_VERSION=3.11-slim-bullseye

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION} as python

# Python 'run' stage
FROM python as python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg2 dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # GIS dependencies
  binutils \
  libproj-dev \
  gdal-bin \
  gcc \
  python3-dev \
  # for CI lint pre-commit checking
  git \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Commented out from example config
# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
# COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# Commented out from example config
# use wheels to install python dependencies
# RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
# 	&& rm -rf /wheels/

# Install poetry following https://python-poetry.org/docs/
RUN pip install poetry


# Using pyproject.toml and poetry.lock, this may end up in the django folder...
COPY pyproject.toml poetry.lock .

# Install local dependencies assuming copy into same folder
# Project initialization:
RUN poetry config virtualenvs.create false && poetry install

# ARG PYTHON_VERSION=3.11-slim-bullseye

# # define an alias for the specfic python version used in this file.
# FROM python:${PYTHON_VERSION} as python
#
#
# # Python build stage
# FROM python as python-build-stage
#
# ENV PYTHONDONTWRITEBYTECODE 1
#
# RUN apt-get update && apt-get install --no-install-recommends -y \
#   # dependencies for building Python packages
#   build-essential \
#   # psycopg2 dependencies
#   libpq-dev \
#   # cleaning up unused files
#   && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
#   && rm -rf /var/lib/apt/lists/*
#
# # Requirements are installed here to ensure they will be cached.
# COPY ./requirements /requirements
#
# # create python dependency wheels
# RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels  \
#   -r /requirements/local.txt -r /requirements/production.txt \
#   && rm -rf /requirements
#
#
# # Python 'run' stage
# FROM python as python-run-stage
#
# ARG BUILD_ENVIRONMENT
# ENV PYTHONUNBUFFERED 1
# ENV PYTHONDONTWRITEBYTECODE 1
#
# RUN apt-get update && apt-get install --no-install-recommends -y \
#   # To run the Makefile
#   make \
#   # psycopg2 dependencies
#   libpq-dev \
#   # Translations dependencies
#   gettext \
#   # Uncomment below lines to enable Sphinx output to latex and pdf
#   # texlive-latex-recommended \
#   # texlive-fonts-recommended \
#   # texlive-latex-extra \
#   # latexmk \
#   # cleaning up unused files
#   && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
#   && rm -rf /var/lib/apt/lists/*
#
# # copy python dependency wheels from python-build-stage
# COPY --from=python-build-stage /usr/src/app/wheels /wheels
#
# # use wheels to install python dependencies
# RUN pip install --no-cache /wheels/* \
#   && rm -rf /wheels
#
EXPOSE 9000
COPY ./compose/local/docs/start /start-docs
RUN sed -i 's/\r$//g' /start-docs
RUN chmod +x /start-docs

COPY . ${APP_HOME}

# WORKDIR /docs
WORKDIR /${APP_HOME}
# Expose MkDocs development server port

# Start development server by default
# ENTRYPOINT ["mkdocs"]
# CMD ["serve", "--dev-addr=0.0.0.0:9000"]
# copy application code to WORKDIR

# ENTRYPOINT ["/entrypoint"]
