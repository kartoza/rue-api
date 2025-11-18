FROM python:3.11-slim AS prod

RUN pip install --no-cache-dir uv
RUN pip install --upgrade pip

# Install dependencies for compiling Python packages and GDAL
RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y g++ gdal-bin libgdal-dev python3-gdal
RUN export GDAL_VERSION=$(gdal-config --version)

# Install rue-lib without pip-installing GDAL
RUN git clone https://github.com/kartoza/rue-lib.git && \
    cd rue-lib && \
    pip install -e .

WORKDIR /app

# Copy the entire project FIRST, because the package root (app/) must exist
COPY . .

# Install dependencies into system Python
RUN uv pip install --system --no-cache .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000

# ============================
# DEV
# ============================
FROM prod AS dev

RUN apt-get update && apt-get install -y \
    openssh-server sudo \
    && rm -rf /var/lib/apt/lists/*

# This directory already exists in some Debian slim images, so use -p
RUN mkdir -p /var/run/sshd

# Install depedencies
RUN uv pip install --system --no-cache ".[dev]"

# Root password
RUN echo "root:docker" | chpasswd

# Allow root login
RUN sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config

# Fix loginuid warning
RUN sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

EXPOSE 8000
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
