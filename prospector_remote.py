#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small standard-library client for a remote Prospector dashboard.

Use this after Phoenix becomes the canonical CRM so local agents do not mutate a
second SQLite database.

Environment:
  PROSPECTOR_REMOTE_URL=https://dashboard.example.com
  PROSPECTOR_AUTH_USER=...
  PROSPECTOR_AUTH_PASSWORD=...

Examples:
  python prospector_remote.py health
  python prospector_remote.py leads
  python prospector_remote.py lead instituto-ferreira-odontologia-rio-claro
  python prospector_remote.py update instituto-ferreira-odontologia-rio-claro '{"status":"publicado"}'
  python prospector_remote.py proposal instituto-ferreira-odontologia-rio-claro
  python prospector_remote.py outreach instituto-ferreira-odontologia-rio-claro

This helper intentionally does not expose outreach/send or lead deletion.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

def _env(key, default=''):
    val = os.environ.get(key, '').strip()
    if not val and sys.platform == 'win32':
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, key)
            winreg.CloseKey(k)
        except Exception:
            val = ''
    return (val or default).strip()


BASE = _env('PROSPECTOR_REMOTE_URL').rstrip('/')
USER = _env('PROSPECTOR_AUTH_USER')
PASSWORD = _env('PROSPECTOR_AUTH_PASSWORD')


def _headers(json_body=False):
    headers = {'Accept': 'application/json'}
    if USER or PASSWORD:
        token = base64.b64encode(('%s:%s' % (USER, PASSWORD)).encode('utf-8')).decode('ascii')
        headers['Authorization'] = 'Basic ' + token
    if json_body:
        headers['Content-Type'] = 'application/json'
    return headers


def request(method, path, body=None, auth=True):
    if not BASE:
        raise SystemExit('PROSPECTOR_REMOTE_URL is required.')
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    headers = _headers(json_body=body is not None) if auth else {'Accept': 'application/json'}
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read().decode('utf-8')
            return res.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {'error': raw or exc.reason}
        return exc.code, payload


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('health')
    sub.add_parser('leads')
    q = sub.add_parser('lead'); q.add_argument('slug')
    q = sub.add_parser('proposal'); q.add_argument('slug')
    q = sub.add_parser('outreach'); q.add_argument('slug')
    q = sub.add_parser('update'); q.add_argument('slug'); q.add_argument('json_changes')
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
    elif args.cmd == 'proposal':
        code, payload = request('GET', '/api/leads/%s/proposal' % urllib.parse.quote(args.slug, safe=''))
    elif args.cmd == 'outreach':
        code, payload = request('GET', '/api/leads/%s/outreach' % urllib.parse.quote(args.slug, safe=''))
    elif args.cmd == 'update':
        try:
            changes = json.loads(args.json_changes)
        except json.JSONDecodeError as exc:
            raise SystemExit('Invalid JSON: %s' % exc)
        if not isinstance(changes, dict):
            raise SystemExit('Update payload must be a JSON object.')
        code, payload = request('PUT', '/api/leads/%s' % urllib.parse.quote(args.slug, safe=''), changes)
    else:
        raise SystemExit(2)

    print(json.dumps({'http': code, 'data': payload}, ensure_ascii=False, indent=2))
    return 0 if 200 <= code < 300 else 1


if __name__ == '__main__':
    sys.exit(main())
