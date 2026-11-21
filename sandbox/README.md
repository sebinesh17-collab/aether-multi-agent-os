# Isolated terminal service

Deploy this on a **separate disposable VM**. The service controls Docker and is therefore effectively root-equivalent on its host. Do not run it on the production database/API host.

## Build and start on the isolated VM

```bash
# From the repository root on the isolated VM
docker build -t aether-sandbox:latest ./sandbox
sudo mkdir -p /srv/aether-workspaces
sudo chmod 0777 /srv/aether-workspaces
export SANDBOX_API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
# Store this token safely; the main application must use the same value.
sudo docker run -d --name aether-sandbox --restart unless-stopped \
  --user 0:0 \
  -e SANDBOX_API_TOKEN="$SANDBOX_API_TOKEN" \
  -e SANDBOX_WORK_ROOT=/srv/aether-workspaces \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /srv/aether-workspaces:/srv/aether-workspaces \
  -p 127.0.0.1:8090:8090 \
  aether-sandbox:latest
```

The Docker socket mount gives this service host-level control. Restrict the VM firewall, do not publish port 8090 to the public internet, route access through a private VPN or authenticated reverse proxy, and set host-level outbound network controls. Use a dedicated VM with no production credentials, backups, or sensitive mounts. Consider gVisor/Kata/Firecracker for stronger isolation of untrusted code.

In the main app `.env`, set `SANDBOX_ENABLED=true`, `SANDBOX_API_URL` to the private URL reachable by the app, and `SANDBOX_API_TOKEN` to the exact same token. The base image contains Python, Node.js/npm, Git, curl, and build tools. Commands run as UID 65534 in read-only-root containers with a 1 GB memory limit, one CPU, and 128 PIDs. Workspace data persists on the isolated VM under `/srv/aether-workspaces`.

This is a restricted convenience runner, not a hostile-code-proof multi-tenant sandbox. Review commands and use a disposable VM.
