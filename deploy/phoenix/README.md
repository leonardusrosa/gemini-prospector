# Phoenix — Legacy Prospector Rollback Archive

Phoenix is no longer part of the active Prospector runtime. The local
Windows checkout owns CRM state, evidence, generation, gates, and deployment
orchestration. Vercel serves public client sites, proposals, and the
production assistant API.

The Phoenix service, database, configuration, and proxy files are retained
temporarily for rollback/archive purposes. Do not reactivate them as part of
normal lead publication.

## Architecture

- Canonical CRM/dashboard: local Windows `prospector.db` and
  `dashboard-server.py` at `http://localhost:8765`.
- Public client sites/proposals/assistant: existing `prospector-sites` Vercel
  project.
- Retired Phoenix service: `prospector-dashboard.service`, formerly bound to
  `127.0.0.1:8765`.
- Preserved Phoenix database: `/var/lib/prospector-dashboard/prospector.db`.
- Preserved Phoenix config: `/var/lib/prospector-dashboard/prospector-config.json`.
- Preserved code checkout: normally `/opt/gemini-prospector`.

The former production wrapper was
`prospector-de-sites/dashboard/dashboard-prod-server.py`. The existing local
`dashboard-server.py` is now the canonical dashboard runtime.

## Legacy remote adapter

`prospector_remote.py` remains in the repository as a legacy/optional remote
CRM adapter. It is not called automatically by `f_status`, `f_salvar`, site
publication, or proposal workflows. Local SQLite mutations must succeed
without Phoenix availability.

The adapter's `REMOTE_SYNC_*` result values are legacy-only semantics. They
must not be used as normal publication outcomes.

## Rollback/reactivation only

Run these steps only after an explicit operator decision to restore Phoenix as
a rollback environment. They are not part of normal Prospector operation.

1. On Phoenix, use the preserved Git checkout. If it is not `/opt/gemini-prospector`, set `PROSPECTOR_REPO_DIR` when running the installer.
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

## Local workflow after cutover

Use the local dashboard and SQLite directly:

```bash
python dashboard-server.py
# open http://localhost:8765
```

The local MCP also targets the same local database:

```bash
python prospector-de-sites/prospector-mcp.py --pasta .
```

Only an explicit rollback or migration check may use `prospector_remote.py`.
Outreach remains a human-reviewed action in the local dashboard.

## Backups

Keep `/var/lib/prospector-dashboard`, `/opt/gemini-prospector`, and the
Phoenix proxy configuration temporarily. Back up the Phoenix SQLite database
and configuration independently of Git. They are rollback/archive data, not
the active CRM source of truth. Never place credential contents in Git or in
operator-facing reports.
