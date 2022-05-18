# Template
FROM python:3.8-slim-buster as main

# Tell Hikka, that it's running docker
# Currently it's used only in .info badge
ENV DOCKER=true

# Suppress weird gitpython error
ENV GIT_PYTHON_REFRESH=quiet

# Do not user pip cache dir
ENV PIP_NO_CACHE_DIR=1

# Install mandatory apt packages
RUN apt update && apt install \
	libcairo2 git -y --no-install-recommends

# Clean the cache
RUN rm -rf /var/lib/apt/lists /var/cache/apt/archives /tmp/*

# Clone the repo
RUN git clone https://github.com/hikariatama/Hikka /Hikka

# Change working directory
WORKDIR /Hikka

# Install mandatory pip requirements
RUN pip install \
	--no-warn-script-location \
	--no-cache-dir \
	-r requirements.txt

# Expose IP address
EXPOSE 8080

# Create data dir
RUN mkdir /data

# Run Hikka
CMD ["python3", "-m", "hikka"]
