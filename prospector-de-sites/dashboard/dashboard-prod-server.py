#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production wrapper for the Prospector dashboard.

Keeps the existing local dashboard server unchanged while adding a safe VPS mode:
- persistent data directory outside the git checkout;
- fail-closed HTTP Basic authentication;
- loopback bind by default for reverse-proxy use;
- health endpoint;
- public proposal URLs work even when the VPS does not contain local site sources;
- local editor/site links are hidden or rewritten to the published URL.

Required environment variables:
  PROSPECTOR_AUTH_USER
  PROSPECTOR_AUTH_PASSWORD

Recommended:
  PROSPECTOR_DATA_DIR=/var/lib/prospector-dashboard
  PROSPECTOR_HOST=127.0.0.1
  PROSPECTOR_PORT=8765
"""

import base64
import hmac
import importlib.util
import json
import os
import sys
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CORE_PATH = os.path.join(HERE, 'dashboard-server.py')

spec = importlib.util.spec_from_file_location('prospector_dashboard_core', CORE_PATH)
if not spec or not spec.loader:
    raise SystemExit('Could not load dashboard-server.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

DATA_DIR = os.path.abspath(os.environ.get('PROSPECTOR_DATA_DIR', os.path.join(HERE, 'data')))
HOST = os.environ.get('PROSPECTOR_HOST', '127.0.0.1').strip() or '127.0.0.1'
PORT = int(os.environ.get('PROSPECTOR_PORT', '8765'))
AUTH_USER = os.environ.get('PROSPECTOR_AUTH_USER', '')
AUTH_PASSWORD = os.environ.get('PROSPECTOR_AUTH_PASSWORD', '')
ALLOW_EMPTY_DB = os.environ.get('PROSPECTOR_ALLOW_EMPTY_DB', '').strip() == '1'

if not AUTH_USER or not AUTH_PASSWORD:
    raise SystemExit('PROSPECTOR_AUTH_USER and PROSPECTOR_AUTH_PASSWORD are required in VPS mode.')

os.makedirs(DATA_DIR, mode=0o700, exist_ok=True)

core.PASTA = DATA_DIR
core.DB = os.path.join(DATA_DIR, 'prospector.db')
core.CONFIG = os.path.join(DATA_DIR, 'prospector-config.json')
core.PORTA = PORT

# The dashboard template immediately switches to /api/leads when the backend is present,
# so an empty bootstrap JSON is sufficient for a clean first render.
dashboard_path = os.path.join(DATA_DIR, 'dashboard.html')
template_path = os.path.join(HERE, 'dashboard-template.html')
if not os.path.isfile(template_path):
    raise SystemExit('dashboard-template.html not found beside dashboard-prod-server.py')
template = open(template_path, encoding='utf-8').read()
bootstrap = json.dumps({'atualizado': '', 'leads': []}, ensure_ascii=False)
open(dashboard_path, 'w', encoding='utf-8').write(template.replace('__DADOS__', bootstrap))

if not os.path.isfile(core.DB) and not ALLOW_EMPTY_DB:
    raise SystemExit(
        'prospector.db is missing from %s. Copy the canonical CRM database before starting, '
        'or explicitly set PROSPECTOR_ALLOW_EMPTY_DB=1 for a new empty CRM.' % DATA_DIR
    )

# On the VPS, proposal.html usually lives in the separate public deploy repository/Vercel,
# not in DATA_DIR/sites. Treat a valid public proposal URL as available.
_original_proposal_meta = core._proposal_meta

def _production_proposal_meta(lead, cfg):
    meta = _original_proposal_meta(lead, cfg)
    meta['exists'] = bool(meta.get('exists') or meta.get('publicUrl'))
    return meta

core._proposal_meta = _production_proposal_meta

PROD_ENHANCEMENT = r'''<script id="prospector-vps-dashboard-enhancement">
(function(){
'use strict';
var bySlug={};
function slugFromPath(value){
  var m=String(value||'').match(/^sites\/([^/]+)\//);
  return m?m[1]:'';
}
function rewriteRemoteActions(){
  document.querySelectorAll('a[href^="sites/"]').forEach(function(a){
    var slug=slugFromPath(a.getAttribute('href'));
    var lead=bySlug[slug];
    var label=(a.textContent||'').trim().toLowerCase();
    if(label.indexOf('editar site')>=0){a.remove();return;}
    if(lead&&lead.urlNova){
      a.href=lead.urlNova;
      a.target='_blank';
      a.rel='noopener';
      if(label==='página')a.textContent='no ar ↗';
    }else{
      a.style.display='none';
    }
  });
  document.querySelectorAll('iframe[src^="sites/"]').forEach(function(frame){
    var slug=slugFromPath(frame.getAttribute('src'));
    var lead=bySlug[slug];
    if(lead&&lead.urlNova&&frame.src!==lead.urlNova)frame.src=lead.urlNova;
  });
}
async function loadRemoteMap(){
  try{
    var r=await fetch('/api/leads',{cache:'no-store'});
    if(!r.ok)return;
    var rows=await r.json();
    (rows||[]).forEach(function(l){if(l&&l.slug)bySlug[l.slug]=l});
    rewriteRemoteActions();
  }catch(e){}
}
new MutationObserver(rewriteRemoteActions).observe(document.documentElement,{childList:true,subtree:true});
loadRemoteMap();
})();
</script>'''

core.DASHBOARD_ENHANCEMENT = core.DASHBOARD_ENHANCEMENT + '\n' + PROD_ENHANCEMENT

_expected_auth = 'Basic ' + base64.b64encode(
    ('%s:%s' % (AUTH_USER, AUTH_PASSWORD)).encode('utf-8')
).decode('ascii')


class ProdApp(core.App):
    def _authorized(self):
        supplied = self.headers.get('Authorization', '')
        return bool(supplied) and hmac.compare_digest(supplied, _expected_auth)

    def _deny(self):
        body = b'Authentication required'
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Prospector Dashboard", charset="UTF-8"')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guard(self):
        if self._authorized():
            return True
        self._deny()
        return False

    def do_GET(self):
        route = self.path.split('?')[0]
        if route == '/api/health':
            return self._json(200, {'ok': True})
        if not self._guard():
            return
        return super().do_GET()

    def do_POST(self):
        if not self._guard():
            return
        return super().do_POST()

    def do_PUT(self):
        if not self._guard():
            return
        return super().do_PUT()

    def do_DELETE(self):
        if not self._guard():
            return
        return super().do_DELETE()


if __name__ == '__main__':
    os.chdir(DATA_DIR)
    core.conexao().close()
    print('Prospector VPS dashboard listening on http://%s:%d' % (HOST, PORT))
    print('Data directory: %s' % DATA_DIR)
    try:
        ThreadingHTTPServer((HOST, PORT), ProdApp).serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
