FROM python:3.8-slim as python-base
#ENV DOCKER=true
ENV GIT_PYTHON_REFRESH=quiet

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install libcairo2 git build-essential -y --no-install-recommends
RUN rm -rf /var/lib/apt/lists /var/cache/apt/archives /tmp/*

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential  \
    gcc \
    python3-dev \
    neofetch \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /data

COPY . /data/Hikka
WORKDIR /data/Hikka

RUN pip install --no-warn-script-location --no-cache-dir -U -r requirements.txt

EXPOSE 8080

USER user

CMD python -m hikka
