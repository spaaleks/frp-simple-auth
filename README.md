# FRP Simple Auth

A lightweight HTTP plugin backend for [frp](https://github.com/fatedier/frp) that adds simple username/password policies with fine-grained proxy restrictions. It runs as a standalone FastAPI service, so credentials and rules stay on your infrastructure.

---

## Features

- YAML-driven policy file (`auth.yml`) with hot-reload support
- Global deny-lists for proxy types, ports, and domains
- User-level allowlists for proxy types, TCP/UDP port ranges, and HTTP(S) domains (wildcards supported)
- FastAPI endpoints compatible with frp’s HTTP plugin (`/handler`, `/health`, `/reload`)
- File watcher + `SIGHUP` handling for zero-downtime config updates
- Environment-variable overrides for listen host/port and config path
- Multi-arch Docker images (linux/amd64, linux/arm64)

---

## Docker

Get up and running quickly by mounting your policy file and letting Docker handle the runtime.

### Standalone

```bash
docker run --rm \
  -p 7005:7005 \
  -v "$(pwd)/auth.yml:/app/auth.yml:ro" \
  -e FRP_AUTH_LISTEN_HOST=0.0.0.0 \
  ghcr.io/<your-org>/frp-simple-auth:latest
```

The container bundles the PyInstaller binary and expects `auth.yml` in `/app`.

### Docker Compose

```yaml
services:
  frp-auth:
    image: spaleks/frp-simple-auth:latest
    # or quay.io/spaleks/frp-simple-auth:latest
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

## Example Workflow

1. Edit `auth.yml` and define users, passwords, and allowed policies.
2. Start the service (locally or via Docker).
3. Configure your frp server to use the HTTP plugin pointing to `/handler`.
4. Reload the service by editing `auth.yml` — changes auto-apply thanks to the file watcher.
5. Monitor `/health` to confirm active users or POST to `/reload` if you need a manual refresh.

### Example frps (`/etc/frp/frps.yaml`)

```yaml
bindAddr: "0.0.0.0"
bindPort: 7000
vhostHTTPPort: 80
vhostHTTPSPort: 443

webServer:
  addr: "0.0.0.0"
  port: 7500
  user: "admin"
  password: "change-me"

httpPlugins:
  - name: "auth"
    addr: "127.0.0.1:7005"     # frp-simple-auth service
    path: "/handler"
    ops:
      - Login
      - NewProxy
```

## Configuration (`auth.yml`)

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

- `globalDeny` – Hard bans evaluated before user-level policies (proxy types, port ranges, domains).
- `proxyTypes` – Allowed frp proxy types (`tcp`, `udp`, `http`, `https`, …).
- `remotePorts` – Single ports or ranges for TCP/UDP proxies.
- `domains` – Allowed HTTP(S) domains; wildcards start with `*.`.

Changes to `auth.yml` are applied instantly via watchdog and `SIGHUP`.

---

## Usage (Local)

1. Clone this repository
2. Copy `.env.example` to `.env` and adjust settings
3. Copy `auth.yml.example` to `auth.yml` and configure users & policies

Run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/frp_simple_auth.py
```

The service listens on `127.0.0.1:7005` by default. Point your frp server’s HTTP plugin to `http://127.0.0.1:7005/handler`.

---

## Environment Variables

### Core
- `FRP_AUTH_CONFIG` – Path to the YAML config (default: `./auth.yml`)
- `FRP_AUTH_LISTEN_HOST` – Host/IP to bind (default: `127.0.0.1`)
- `FRP_AUTH_LISTEN_PORT` – Port to bind (default: `7005`)

### Logging
- `LOGLEVEL` – Python log level (`INFO`, `DEBUG`, …)

### Misc
- `.env` support via `python-dotenv`; any key in `.env` overrides runtime defaults.

---

## Development

1. Create a virtualenv & install dependencies.
2. Run `uvicorn frp_simple_auth:app --reload` for live FastAPI reloading.
3. Use `pytest` or add unit tests for policy helpers as needed.

PyInstaller builds emit outputs into `dist/`; temporary build artifacts live in `build/` (both ignored via `.gitignore`).

Optional helper scripts:

- `bin/buildCurrentPlatform.sh` builds a PyInstaller binary for your current machine.
- `bin/buildAnyPlatform.sh` cross-builds Linux binaries via Docker (amd64, arm64).

---

## License

MIT
