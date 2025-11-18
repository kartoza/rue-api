FROM python:3.11-slim AS prod

RUN pip install --no-cache-dir uv

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

# Root password
RUN echo "root:docker" | chpasswd

# Allow root login
RUN sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config

# Fix loginuid warning
RUN sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

EXPOSE 8000
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
