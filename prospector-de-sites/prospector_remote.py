#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standard-library client for a remote Prospector dashboard.

Provides remote query, update, and deterministic synchronization between
local canonical SQLite and the remote production CRM.

Environment:
  PROSPECTOR_REMOTE_URL=https://dashboard.example.com
  PROSPECTOR_AUTH_USER=...
  PROSPECTOR_AUTH_PASSWORD=...
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

SYNC_FIELDS = ['status', 'nota', 'avaliacoes', 'urlNova', 'endCliente', 'telefone', 'whatsapp']


def _env(key, default=''):
    val = os.environ.get(key, '').strip()
    if sys.platform == 'win32' and (not val or (key == 'PROSPECTOR_AUTH_PASSWORD' and len(val) < 20)):
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ)
            reg_val, _ = winreg.QueryValueEx(k, key)
            winreg.CloseKey(k)
            if reg_val and len(reg_val) >= 20:
                val = reg_val.strip()
        except Exception:
            pass
    return (val or default).strip()


def get_remote_config():
    return {
        'base': _env('PROSPECTOR_REMOTE_URL').rstrip('/'),
        'user': _env('PROSPECTOR_AUTH_USER'),
        'password': _env('PROSPECTOR_AUTH_PASSWORD'),
    }


def redact(text, extra_secrets=None):
    if not text:
        return text
    s = str(text)
    pw = get_remote_config().get('password')
    if pw and len(pw) > 3:
        s = s.replace(pw, '[REDACTED]')
    if extra_secrets:
        for sec in extra_secrets:
            if sec and len(sec) > 3:
                s = s.replace(sec, '[REDACTED]')
    s = re.sub(r'Basic\s+[A-Za-z0-9+/=]+', 'Basic [REDACTED]', s)
    s = re.sub(r'(?:password|secret|token)\s*[:=]\s*([^\s,;\'"]+)', r'password: [REDACTED]', s, flags=re.IGNORECASE)
    s = re.sub(r'Authorization:\s*[^\r\n]+', 'Authorization: [REDACTED]', s, flags=re.IGNORECASE)
    return s


def _headers(json_body=False, user=None, password=None):
    cfg = get_remote_config()
    u = user if user is not None else cfg['user']
    p = password if password is not None else cfg['password']
    headers = {'Accept': 'application/json'}
    if u or p:
        token = base64.b64encode(f'{u}:{p}'.encode('utf-8')).decode('ascii')
        headers['Authorization'] = 'Basic ' + token
    if json_body:
        headers['Content-Type'] = 'application/json'
    return headers


def request(method, path, body=None, auth=True, base_url=None, user=None, password=None):
    cfg = get_remote_config()
    base = (base_url or cfg['base']).rstrip('/')
    if not base:
        return 0, {'error': 'PROSPECTOR_REMOTE_URL is required.'}
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    headers = _headers(json_body=body is not None, user=user, password=password) if auth else {'Accept': 'application/json'}
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read().decode('utf-8')
            return res.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {'error': redact(raw or exc.reason)}
        return exc.code, payload
    except Exception as exc:
        return 0, {'error': redact(str(exc))}


def _normalize_str(v):
    return re.sub(r'\s+', ' ', str(v or '').strip().lower())


def _normalize_phone(v):
    return re.sub(r'\D', '', str(v or ''))


def _statuses_match(local_st, remote_st):
    norm = {
        'publicado': 'published', 'published': 'published',
        'qualificado': 'qualified', 'qualified': 'qualified',
        'novo': 'discovered', 'discovered': 'discovered',
        'redesenhado': 'redesigned', 'redesigned': 'redesigned',
        'proposta': 'contactado', 'contactado': 'contactado',
        'descartado': 'perdido', 'perdido': 'perdido',
    }
    return norm.get(str(local_st).lower()) == norm.get(str(remote_st).lower())


def compare_critical_fields(canonical_lead, remote_lead):
    divs = {}
    if not _statuses_match(canonical_lead.get('status'), remote_lead.get('status')):
        divs['status'] = {'canonical': canonical_lead.get('status'), 'remote': remote_lead.get('status')}
    for f in ['nota']:
        cv, rv = canonical_lead.get(f), remote_lead.get(f)
        if cv is not None and rv is not None and round(float(cv), 1) != round(float(rv), 1):
            divs[f] = {'canonical': cv, 'remote': rv}
    for f in ['avaliacoes']:
        cv, rv = canonical_lead.get(f), remote_lead.get(f)
        if cv is not None and rv is not None and int(cv) != int(rv):
            divs[f] = {'canonical': cv, 'remote': rv}
    for f in ['urlNova']:
        cv, rv = (canonical_lead.get(f) or '').strip().rstrip('/'), (remote_lead.get(f) or '').strip().rstrip('/')
        if cv != rv:
            divs[f] = {'canonical': canonical_lead.get(f), 'remote': remote_lead.get(f)}
    for f in ['endCliente']:
        if _normalize_str(canonical_lead.get(f)) != _normalize_str(remote_lead.get(f)):
            divs[f] = {'canonical': canonical_lead.get(f), 'remote': remote_lead.get(f)}
    for f in ['telefone', 'whatsapp']:
        if _normalize_phone(canonical_lead.get(f)) != _normalize_phone(remote_lead.get(f)):
            divs[f] = {'canonical': canonical_lead.get(f), 'remote': remote_lead.get(f)}
    return divs


def sync_lead(slug, db_path=None, base_url=None, user=None, password=None):
    cfg = get_remote_config()
    base = (base_url or cfg['base']).rstrip('/')
    if not base:
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_NOT_CONFIGURED',
                'status_result': 'REMOTE_SYNC_SKIPPED', 'error': 'PROSPECTOR_REMOTE_URL not configured'}
    dbp = db_path or 'prospector.db'
    if not os.path.exists(dbp):
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_FAILED',
                'status_result': 'REMOTE_SYNC_PENDING', 'error': f'Canonical DB {dbp} not found'}

    conn = sqlite3.connect(dbp)
    c = conn.cursor()
    c.execute('SELECT %s FROM leads WHERE slug=?' % ','.join(SYNC_FIELDS), (slug,))
    row = c.fetchone()
    conn.close()

    if not row:
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_FAILED',
                'status_result': 'REMOTE_SYNC_PENDING', 'error': f'Lead {slug} not found in canonical DB'}

    canonical_lead = dict(zip(SYNC_FIELDS, row))
    payload = {k: canonical_lead[k] for k in SYNC_FIELDS if canonical_lead[k] is not None}

    # 1. Attempt remote PUT
    code, res = request('PUT', f'/api/leads/{urllib.parse.quote(slug, safe="")}',
                        body=payload, auth=True, base_url=base, user=user, password=password)
    if code != 200 or not (isinstance(res, dict) and res.get('ok')):
        err = res.get('error') if isinstance(res, dict) else res
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_FAILED',
                'status_result': 'REMOTE_SYNC_PENDING', 'http_code': code, 'error': f'Remote PUT failed: {redact(err)}'}

    # 2. Read back remote record
    g_code, remote_rows = request('GET', '/api/leads', auth=True, base_url=base, user=user, password=password)
    if g_code != 200 or not isinstance(remote_rows, list):
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_FAILED',
                'status_result': 'REMOTE_SYNC_PENDING', 'http_code': g_code, 'error': 'Remote read-back failed'}

    remote_lead = next((x for x in remote_rows if x.get('slug') == slug), None)
    if not remote_lead:
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_FAILED',
                'status_result': 'REMOTE_SYNC_PENDING', 'error': f'Lead {slug} missing from remote read-back'}

    # 3. Compare critical fields
    divergences = compare_critical_fields(canonical_lead, remote_lead)
    if divergences:
        return {'ok': False, 'slug': slug, 'sync_status': 'REMOTE_SYNC_FAILED',
                'status_result': 'REMOTE_SYNC_PENDING', 'divergences': divergences,
                'error': f'Field mismatch after sync: {divergences}'}

    return {'ok': True, 'slug': slug, 'sync_status': 'REMOTE_SYNC_OK',
            'status_result': 'PUBLISHED + REMOTE_SYNC_OK', 'synced_fields': list(payload.keys())}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('health')
    sub.add_parser('leads')
    for name in ['lead', 'proposal', 'outreach', 'sync']:
        sub.add_parser(name).add_argument('slug')
    q = sub.add_parser('update')
    q.add_argument('slug')
    q.add_argument('json_changes')
    args = p.parse_args()

    if args.cmd == 'health':
        code, payload = request('GET', '/api/health', auth=False)
    elif args.cmd == 'leads':
        code, payload = request('GET', '/api/leads')
    elif args.cmd == 'lead':
        code, rows = request('GET', '/api/leads')
        payload = next((x for x in (rows or []) if x.get('slug') == args.slug), None) if code == 200 else rows
        if code == 200 and payload is None:
            code, payload = 404, {'error': 'lead not found'}
    elif args.cmd in ('proposal', 'outreach'):
        code, payload = request('GET', f'/api/leads/{urllib.parse.quote(args.slug, safe="")}/{args.cmd}')
    elif args.cmd == 'update':
        try:
            changes = json.loads(args.json_changes)
            if not isinstance(changes, dict):
                raise ValueError()
        except Exception:
            raise SystemExit('Invalid JSON object payload')
        code, payload = request('PUT', f'/api/leads/{urllib.parse.quote(args.slug, safe="")}', changes)
    elif args.cmd == 'sync':
        res = sync_lead(args.slug)
        code, payload = (200 if res.get('ok') else 500), res
    else:
        raise SystemExit(2)

    print(redact(json.dumps({'http': code, 'data': payload}, ensure_ascii=False, indent=2)))
    return 0 if 200 <= code < 300 else 1


if __name__ == '__main__':
    sys.exit(main())
