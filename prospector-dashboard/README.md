# Prospector Dashboard — protected preview candidate

This app is a separate hosted-dashboard candidate for the Prospector CRM.

Current authority rules:

- `../prospector.db` remains the canonical CRM.
- Supabase is a one-way `PREVIEW_COPY` only.
- Hosted writes default to disabled (`CRM_WRITE_ENABLED=false`).
- No outreach send endpoint is implemented.
- No private contract document is exposed.
- Deployment is intentionally outside this stage.

## Local checks

```powershell
npm install
npm run typecheck
npm run build
python scripts/migrate-sqlite-to-postgres.py --dry-run
```

`--apply` is fail-closed and additionally requires `--confirm` plus server-side Supabase credentials.
