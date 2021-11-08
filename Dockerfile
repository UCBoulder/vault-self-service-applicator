FROM registry.access.redhat.com/ubi8-minimal:8.4-212 as base

ENV APP_ROOT=/usr/src/app \
    PYTHON_PKG=python39 \
    PYTHON_VERSION=3.9 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=en_US.UTF-8 \
    PIP_NO_CACHE_DIR=off \
    PIPENV_VENV_IN_PROJECT=1

ENV PATH=${APP_ROOT}/.local/bin:${PATH}

# pipenv complains if you don't install which
RUN microdnf install -y which shadow-utils ${PYTHON_PKG}{,-devel,-setuptools,-pip}

WORKDIR ${APP_ROOT}

# use pipenv to create venv in APP_ROOT
RUN pip${PYTHON_VERSION} install pipenv=="v2021.5.29" && \
    pipenv --python ${PYTHON_VERSION}

COPY ["Pipfile", "Pipfile.lock", "./"]
RUN pipenv install --deploy

# Install dev-deps and run tests
FROM base as test

RUN pipenv install --dev --deploy

COPY . .
RUN pipenv run pylint --disable=consider-using-f-string self_service
RUN pipenv run pylint --disable=missing-docstring,duplicate-code tests
RUN pipenv run pytest

# Throw away dev-deps and any testing artifacts for final image
FROM base

COPY . .
CMD ["/usr/src/app/.venv/bin/python", "/usr/src/app/entrypoint.py"]
