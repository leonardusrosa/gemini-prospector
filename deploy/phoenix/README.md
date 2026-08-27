# Phoenix — Prospector Dashboard

This deployment keeps the public client previews on Vercel and runs only the private CRM/dashboard on the Phoenix VPS.

## Architecture

- Public client sites/proposals: existing `prospector-sites` Vercel project.
- Private dashboard/backend: Phoenix, bound to `127.0.0.1:8765`.
- Public access to the dashboard: existing Phoenix reverse proxy + HTTPS.
- Dashboard protection: application-level HTTP Basic Auth from `/etc/prospector-dashboard.env`.
- CRM database: `/var/lib/prospector-dashboard/prospector.db`.
- Dashboard config: `/var/lib/prospector-dashboard/prospector-config.json`.
- Code: the GitHub checkout, normally `/opt/gemini-prospector`.

The production wrapper is `prospector-de-sites/dashboard/dashboard-prod-server.py`. The existing local `dashboard-server.py` remains unchanged.

## Important: one writable CRM

After migration, the Phoenix database must be treated as the canonical CRM. Do not keep the local Windows SQLite database and the Phoenix SQLite database independently writable; they will diverge.

Local agents should use `prospector_remote.py` against the Phoenix API after the cutover instead of directly mutating a second `prospector.db`.

## First deployment

1. On Phoenix, use the Git checkout that is already authenticated to GitHub. If it is not `/opt/gemini-prospector`, set `PROSPECTOR_REPO_DIR` when running the installer.
2. Pull `main`.
3. Run `deploy/phoenix/install-or-update.sh` as root. The first run creates `/etc/prospector-dashboard.env` and exits so secrets can be filled safely.
4. Put a long random dashboard password in `/etc/prospector-dashboard.env`.
5. Put the existing Evolution API settings/key in that same root-only env file. Do not commit the key.
6. Securely copy the current local `prospector.db` to `/var/lib/prospector-dashboard/prospector.db`.
7. Securely copy the current local `prospector-config.json` to `/var/lib/prospector-dashboard/prospector-config.json` if present.
8. Run the installer again. It enables/restarts `prospector-dashboard.service` and verifies `/api/health` locally.
9. Add the reverse-proxy route using `nginx-location.conf.example` or the equivalent configuration in Phoenix's existing proxy.
10. Enable HTTPS for the chosen dashboard hostname before using credentials over the network.

## One-time database transfer

The CRM DB is intentionally ignored by Git and must never be committed to either repository.

Example from the local machine, substituting the actual Phoenix SSH host:

```bash
scp prospector.db user@phoenix:/tmp/prospector.db
scp prospector-config.json user@phoenix:/tmp/prospector-config.json
```

Then on Phoenix:

```bash
sudo install -o prospector -g prospector -m 0600 /tmp/prospector.db /var/lib/prospector-dashboard/prospector.db
sudo install -o prospector -g prospector -m 0600 /tmp/prospector-config.json /var/lib/prospector-dashboard/prospector-config.json
rm -f /tmp/prospector.db /tmp/prospector-config.json
```

Use the VPS's existing secure transfer workflow if it already has one.

## Verification

Backend health, no auth required and no CRM data returned:

```bash
curl -fsS http://127.0.0.1:8765/api/health
```

Expected:

```json
{"ok": true}
```

Authenticated local check:

```bash
curl -u "$PROSPECTOR_AUTH_USER:$PROSPECTOR_AUTH_PASSWORD" http://127.0.0.1:8765/api/leads
```

External verification must use the HTTPS dashboard hostname.

## Public proposal handling

The VPS does not need a copy of `sites/<slug>/...`. `dashboard-prod-server.py` treats a valid public proposal URL as available and removes/replaces local-only site/editor actions at runtime. Published `urlNova` links continue to point to Vercel.

## Local agent after cutover

Set locally:

```text
PROSPECTOR_REMOTE_URL=https://<dashboard-hostname>
PROSPECTOR_AUTH_USER=<dashboard-user>
PROSPECTOR_AUTH_PASSWORD=<dashboard-password>
```

Then use, for example:

```bash
python prospector_remote.py health
python prospector_remote.py lead instituto-ferreira-odontologia-rio-claro
python prospector_remote.py update instituto-ferreira-odontologia-rio-claro '{"status":"publicado"}'
```

`prospector_remote.py` deliberately does not expose deletion or outreach sending. Outreach remains a human-reviewed action in the dashboard.

## Backups

Back up `/var/lib/prospector-dashboard/prospector.db` independently of Git. SQLite is the operational state and Git is only the application code.
