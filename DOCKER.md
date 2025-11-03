![Docker](https://img.shields.io/badge/Docker-Multi--Arch-blue?style=for-the-badge&logo=docker)

# FRP Simple Auth (Docker)

A lightweight FastAPI service that implements FRP’s HTTP plugin for authentication. Define users and per-proxy policies in YAML, reload on the fly, and keep credentials on your own infrastructure.

---

## Highlights

- Hot-reloadable `auth.yml` with global deny-lists for proxy types, ports, and domains.
- Supports FRP plugin operations `Login` and `NewProxy`.
- Multi-arch images for `linux/amd64` and `linux/arm64`.
- PyInstaller static binary bundled inside the container; runtime based on Debian slim.

---

## Quick Start

```bash
docker run --rm \
  -p 7005:7005 \
  -v "$(pwd)/auth.yml:/app/auth.yml:ro" \
  -e FRP_AUTH_LISTEN_HOST=0.0.0.0 \
  -e FRP_AUTH_CONFIG=/app/auth.yml \
  spaleks/frp-simple-auth:latest
```

- Default listen port inside the container: `7005`
- Health check: `GET /health`
- Manual reload: `POST /reload`
- Set `FRP_AUTH_CONFIG` if you mount the config somewhere else.

---

## Docker Compose

```yaml
services:
  frp-auth:
    image: spaleks/frp-simple-auth:latest
    container_name: frp-simple-auth
    restart: unless-stopped
    environment:
      - FRP_AUTH_LISTEN_HOST=0.0.0.0
      - FRP_AUTH_LISTEN_PORT=7005
      - FRP_AUTH_CONFIG=/app/auth.yml
    volumes:
      - ./auth.yml:/app/auth.yml:ro
    ports:
      - "7005:7005"
```

---

## FRP Server Example (`frps.yaml`)

```yaml
httpPlugins:
  - name: auth
    addr: 127.0.0.1:7005
    path: /handler
    ops:
      - Login
      - NewProxy
```

Ensure your FRP server can reach the container (same host or network route).

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRP_AUTH_CONFIG` | `./auth.yml` | Path to the YAML policy file |
| `FRP_AUTH_LISTEN_HOST` | `127.0.0.1` | Bind address |
| `FRP_AUTH_LISTEN_PORT` | `7005` | Service port |
| `LOGLEVEL` | `INFO` | Python logging level |

`.env` files are honored thanks to `python-dotenv`.

---

## Configuration Snippet (`auth.yml`)

```yaml
globalDeny:
  proxyTypes: ["udp"]
  remotePorts: ["1-1023"]
  domains:
    - "*.blocked.example"

users:
  - user: "alice"
    password: "s3cret"
    allow:
      proxyTypes: ["http", "https"]
      remotePorts: ["2000-2100", "5432"]
      domains:
        - "example.com"
        - "*.internal.example.com"
```

Changes to `auth.yml` trigger an automatic reload (inotify + SIGHUP).

---

## Binaries

The image bundles the PyInstaller-built binary at `/usr/local/bin/frp-simple-auth`. GitHub Releases also publish standalone Linux binaries (amd64 & arm64) if you prefer running without Docker.

---

## Source & License

- Source: [github.com/spaleks/frp-simple-auth](https://github.com/spaleks/frp-simple-auth)
- License: MIT
