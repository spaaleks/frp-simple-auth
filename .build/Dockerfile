# syntax=docker/dockerfile:1.6

FROM --platform=$TARGETPLATFORM python:3.12-slim AS builder
ARG TARGETPLATFORM
WORKDIR /build
RUN apt-get update \
 && apt-get install -y --no-install-recommends binutils \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && python -m pip install -r requirements.txt pyinstaller
COPY src ./src
RUN pyinstaller --onefile --name frp-simple-auth src/frp_simple_auth.py

FROM debian:trixie-slim AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates libmagic1 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY auth.yml.example /app/auth.yml.example
COPY --from=builder /build/dist/frp-simple-auth /usr/local/bin/frp-simple-auth
ENV FRP_AUTH_CONFIG=/app/auth.yml \
    FRP_AUTH_LISTEN_HOST=0.0.0.0 \
    FRP_AUTH_LISTEN_PORT=7005 \
    PATH=/usr/local/bin:$PATH
EXPOSE 7005
ENTRYPOINT ["/usr/local/bin/frp-simple-auth"]
