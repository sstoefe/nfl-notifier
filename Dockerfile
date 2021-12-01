FROM python:3-slim

RUN apt update && apt install -y \
    locales \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && pip install poetry \
    && apt clean autoclean \
    && apt autoremove -y \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/

WORKDIR /app
COPY poetry.lock pyproject.toml credentials.json token.pickle /app/
COPY config_docker.toml /app/config.toml
COPY nfl_notifier /app/nfl_notifier/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev