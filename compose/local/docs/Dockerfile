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

RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev

WORKDIR ${APP_HOME}

# Worth fixing so only minimal needed is used if possible
# COPY pyproject.toml poetry.lock mkdocs.yml docs .

COPY . .

RUN pip install poetry

EXPOSE 8000

RUN poetry config virtualenvs.create false && poetry install --with docs

ENTRYPOINT [ "mkdocs" ]
CMD ["serve", "-f", "/app/mkdocs.yml", "--dev-addr=0.0.0.0:8000"]
