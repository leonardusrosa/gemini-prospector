#!/usr/bin/env python3
"""Post-generation patch: add Save Draft / Publish Changes to Prospector editor.

The generated editor remains usable as a standalone HTML editor. Publishing only
works when the editor publish API is available; local users should run
`python editor_server.py` from the workspace root.
"""

from __future__ import annotations

import html as html_lib
import pathlib
import re

START = "<!-- PROSPECTOR-PUBLISH-START -->"
END = "<!-- PROSPECTOR-PUBLISH-END -->"

PUBLISH_LAYER = r'''<!-- PROSPECTOR-PUBLISH-START -->
<style id="pe-publish-style" data-pe-ui>
#pe-draft{background:#374151;color:#fff}
#pe-publish{background:#16a34a;color:#fff}
#pe-publish-status{font:12px/1.25 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:260px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.82}
#pe-publish-status.pe-error{color:#fecaca;opacity:1}
#pe-publish-status.pe-ok{color:#bbf7d0;opacity:1}
#pe-export{background:#374151!important;color:#fff!important}
@media(max-width:900px){#pe-publish-status{display:none}}
</style>
<script id="pe-publish-script" data-pe-ui>
(function(){
'use strict';
var root=document.documentElement;
var target=root.getAttribute('data-pe-publish-target')||'';
var api=(root.getAttribute('data-pe-publish-api')||'/api/editor').replace(/\/$/,'');
var draftKey='prospector-editor-draft:'+target;
var restoredKey='prospector-editor-restored:'+target+':'+location.pathname;
var tokenKey='prospector-editor-token:'+target;
var draftBtn=document.getElementById('pe-draft');
var publishBtn=document.getElementById('pe-publish');
var statusEl=document.getElementById('pe-publish-status');

function setStatus(text,kind){
  if(!statusEl)return;
  statusEl.textContent=text||'';
  statusEl.classList.remove('pe-error','pe-ok');
  if(kind)statusEl.classList.add(kind==='error'?'pe-error':'pe-ok');
}
function cleanPublicDocument(){
  var doc=document.documentElement.cloneNode(true);
  Array.from(doc.querySelectorAll('[data-pe-ui],#pe-style,#pe-script,#pe-publish-style,#pe-publish-script')).forEach(function(n){n.remove()});
  Array.from(doc.querySelectorAll('[contenteditable]')).forEach(function(n){n.removeAttribute('contenteditable')});
  Array.from(doc.querySelectorAll('.pe-hover,.pe-selected')).forEach(function(n){n.classList.remove('pe-hover','pe-selected')});
  Array.from(doc.querySelectorAll('[data-pe-bound-text]')).forEach(function(n){n.removeAttribute('data-pe-bound-text')});
  doc.removeAttribute('data-pe-publish-target');
  doc.removeAttribute('data-pe-publish-api');
  var body=doc.querySelector('body');
  if(body)body.classList.remove('pe-editing','pe-previewing');
  return '<!DOCTYPE html>\n'+doc.outerHTML;
}
function snapshotEditorDocument(){
  var doc=document.documentElement.cloneNode(true);
  Array.from(doc.querySelectorAll('[contenteditable]')).forEach(function(n){n.removeAttribute('contenteditable')});
  Array.from(doc.querySelectorAll('.pe-hover,.pe-selected')).forEach(function(n){n.classList.remove('pe-hover','pe-selected')});
  var panel=doc.querySelector('#pe-panel');if(panel)panel.classList.remove('pe-open');
  return '<!DOCTYPE html>\n'+doc.outerHTML;
}
function token(){return sessionStorage.getItem(tokenKey)||''}
function askToken(){
  var t=window.prompt('Token de acesso do editor para este site:','')||'';
  if(t)sessionStorage.setItem(tokenKey,t);
  return t;
}
async function request(action,payload,retry){
  var headers={'Content-Type':'application/json'};
  var t=token();if(t)headers.Authorization='Bearer '+t;
  var res;
  try{
    res=await fetch(api+'/'+action,{method:'POST',headers:headers,body:JSON.stringify(payload)});
  }catch(err){
    throw new Error('Servidor de publicação indisponível. Em localhost, execute: python editor_server.py');
  }
  var data={};try{data=await res.json()}catch(e){}
  if(res.status===401&&retry!==false){
    if(!askToken())throw new Error(data.error||'Autorização necessária.');
    return request(action,payload,false);
  }
  if(!res.ok||!data.success)throw new Error(data.error||('Falha HTTP '+res.status));
  return data;
}
async function saveDraft(){
  if(!target){setStatus('Editor sem target de publicação','error');return}
  try{
    localStorage.setItem(draftKey,snapshotEditorDocument());
    setStatus('Rascunho salvo neste navegador','ok');
    try{
      await request('draft',{target:target,html:cleanPublicDocument()},true);
      setStatus('Rascunho salvo','ok');
    }catch(serverErr){
      // Browser persistence is still valid; do not turn a useful local draft into a failure.
      setStatus('Rascunho salvo no navegador · backend indisponível','ok');
    }
  }catch(err){setStatus(err.message||String(err),'error')}
}
async function publish(){
  if(!target){setStatus('Editor sem target de publicação','error');return}
  if(!window.confirm('Publicar estas alterações agora? O site público/local será atualizado.'))return;
  publishBtn.disabled=true;setStatus('Publicando…');
  try{
    var data=await request('publish',{target:target,html:cleanPublicDocument(),confirmed:true},true);
    localStorage.removeItem(draftKey);
    sessionStorage.removeItem(restoredKey);
    var msg=data.status==='published_local'?'Publicado no localhost':data.status==='published_git'?'Publicado e enviado ao Git':'Sem alterações para publicar';
    if(data.commit)msg+=' · '+data.commit.slice(0,8);
    setStatus(msg,'ok');
    if(data.publicUrl)publishBtn.title='Site atualizado: '+data.publicUrl;
  }catch(err){setStatus(err.message||String(err),'error')}
  finally{publishBtn.disabled=false}
}

if(draftBtn)draftBtn.addEventListener('click',saveDraft);
if(publishBtn)publishBtn.addEventListener('click',publish);

// Restore the browser-side draft once per page load when the user explicitly agrees.
try{
  var saved=localStorage.getItem(draftKey);
  if(saved&&!sessionStorage.getItem(restoredKey)){
    sessionStorage.setItem(restoredKey,'1');
    setTimeout(function(){
      if(window.confirm('Existe um rascunho salvo neste navegador para este site. Restaurar?')){
        document.open();document.write(saved);document.close();
      }
    },0);
  }
}catch(e){}
})();
</script>
<!-- PROSPECTOR-PUBLISH-END -->'''


def strip_existing(html: str) -> str:
    return re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)


def canonical_target(source: pathlib.Path) -> str:
    parts = list(source.parts)
    lowered = [p.lower() for p in parts]
    if "sites" not in lowered:
        raise ValueError("Source must live under sites/<slug>/<slug>.html for publish support")
    idx = lowered.index("sites")
    tail = parts[idx:]
    if len(tail) != 3:
        raise ValueError("Canonical editor publish source must be sites/<slug>/<slug>.html")
    slug = tail[1]
    if pathlib.Path(tail[2]).stem != slug or pathlib.Path(tail[2]).suffix.lower() != ".html":
        raise ValueError("Canonical editor publish source must be sites/<slug>/<slug>.html")
    return pathlib.PurePosixPath(*tail).as_posix()


def patch_editor(output: pathlib.Path, source: pathlib.Path) -> None:
    text = strip_existing(output.read_text(encoding="utf-8"))
    target = canonical_target(source)

    # Keep target metadata in the editor document only. cleanPublicDocument removes it.
    if "data-pe-publish-target=" in text:
        text = re.sub(r'\sdata-pe-publish-target=("[^"]*"|\'[^\']*\')', "", text, count=1)
    if "data-pe-publish-api=" in text:
        text = re.sub(r'\sdata-pe-publish-api=("[^"]*"|\'[^\']*\')', "", text, count=1)
    text = re.sub(
        r"<html\b",
        '<html data-pe-publish-target="%s" data-pe-publish-api="/api/editor"' % html_lib.escape(target, quote=True),
        text,
        count=1,
        flags=re.I,
    )

    # Add explicit workflow controls. Export remains a secondary portability action.
    if 'id="pe-draft"' not in text:
        needle = '<button id="pe-export" type="button">Exportar página</button>'
        controls = (
            '<button id="pe-draft" type="button">Salvar rascunho</button>\n'
            '  <button id="pe-publish" type="button">Publicar alterações</button>\n'
            '  <span id="pe-publish-status" aria-live="polite"></span>\n  '
            + needle
        )
        if needle not in text:
            raise ValueError("Could not find editor export control for publish patch")
        text = text.replace(needle, controls, 1)

    marker = "<!-- PROSPECTOR-EDITOR-END -->"
    if marker not in text:
        raise ValueError("Generated editor marker not found")
    text = text.replace(marker, PUBLISH_LAYER + "\n" + marker, 1)
    output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("editor")
    p.add_argument("source")
    ns = p.parse_args()
    patch_editor(pathlib.Path(ns.editor), pathlib.Path(ns.source))
    print(f"Draft/publish controls enabled in: {ns.editor}")
