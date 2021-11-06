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

#RUN useradd -d ${APP_ROOT} -M -N -u 1001 -g 0 applicator
WORKDIR ${APP_ROOT}
#RUN chown -R 1001:0 ${APP_ROOT}
#USER 1001

# For some reason, regardless of the installation location, this defaults to:
# FileNotFoundError: [Errno 2] No such file or directory: '/usr/lib/python3.9/site-packages/pip/_vendor/certifi/cacert.pem'
#ENV REQUESTS_CA_BUNDLE=${APP_ROOT}/.local/lib/pyhton3.9/site-packages/pip/_vendor/certifi

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

# Set pythonpath in case container runs as different user later
#ENV PYTHONPATH=${APP_ROOT}/.local/lib/python${PYTHON_VERSION}

COPY . .
#CMD ["/usr/src/app/.local/bin/pipenv", "run", "python", "./entrypoint.py"]
<<<<<<< Updated upstream
CMD ["/usr/src/app/.venv/bin/python", "./entrypoint.py"]
=======
CMD ["/usr/src/app/.venv/bin/python", "/usr/src/app/entrypoint.py"]
>>>>>>> Stashed changes
