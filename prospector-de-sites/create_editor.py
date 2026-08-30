#!/usr/bin/env python3
'''Generate a client-safe visual editor for any Prospector static site.

Usage:
    python create_editor.py sites/acme/acme.html
    python create_editor.py sites/acme/acme.html --output sites/acme/acme-editor.html

The editor exposes content/media/action properties only. It intentionally does
not expose arbitrary HTML, CSS or JavaScript editing.
'''

from __future__ import annotations

import argparse
import html as html_lib
import pathlib
import re

START = "<!-- PROSPECTOR-EDITOR-START -->"
END = "<!-- PROSPECTOR-EDITOR-END -->"

EDITOR_LAYER = r'''<!-- PROSPECTOR-EDITOR-START -->
<style id="pe-style">
:root{--pe-bg:#111827;--pe-panel:#fff;--pe-line:#d1d5db;--pe-accent:#16a34a;--pe-blue:#2563eb;--pe-text:#111827;--pe-muted:#6b7280}
#pe-bar{position:fixed;top:0;left:0;right:0;z-index:2147483646;background:var(--pe-bg);color:#fff;font:13px/1.25 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;align-items:center;gap:12px;padding:9px 14px;box-shadow:0 2px 10px rgba(0,0,0,.28)}
#pe-bar strong{white-space:nowrap}#pe-bar .pe-help{opacity:.75;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
#pe-bar button,#pe-panel button{font:inherit;border:0;border-radius:7px;padding:8px 12px;font-weight:700;cursor:pointer}
#pe-export{background:var(--pe-accent);color:#fff}.pe-secondary{background:#374151;color:#fff}
body.pe-editing{margin-top:48px!important}.pe-hover{outline:2px dashed #22c55e!important;outline-offset:2px;cursor:pointer!important}
.pe-selected{outline:2px solid var(--pe-blue)!important;outline-offset:2px}[contenteditable="true"]{cursor:text!important}[contenteditable="true"]:focus{outline:2px solid var(--pe-blue)!important;outline-offset:2px}
#pe-panel{position:fixed;z-index:2147483647;top:58px;right:12px;width:min(380px,calc(100vw - 24px));max-height:calc(100vh - 70px);overflow:auto;background:var(--pe-panel);color:var(--pe-text);border:1px solid var(--pe-line);border-radius:12px;box-shadow:0 18px 50px rgba(0,0,0,.24);font:13px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:none}
#pe-panel.pe-open{display:block}#pe-panel header{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid #e5e7eb}#pe-panel header strong{font-size:14px}#pe-close{background:transparent!important;color:#374151!important;padding:4px 8px!important;font-size:18px!important}
#pe-form{padding:14px 16px 16px}.pe-field{display:block;margin:0 0 12px}.pe-field>span{display:block;font-weight:700;margin-bottom:5px}.pe-field input,.pe-field select,.pe-field textarea{box-sizing:border-box;width:100%;border:1px solid #cbd5e1;border-radius:7px;padding:8px 9px;background:#fff;color:#111827;font:inherit}.pe-field textarea{min-height:72px;resize:vertical}.pe-field input:disabled{background:#f3f4f6;color:#6b7280}
.pe-check{display:flex;gap:8px;align-items:flex-start;margin:10px 0}.pe-check input{margin-top:3px}.pe-note{font-size:12px;color:var(--pe-muted);margin:-4px 0 12px}.pe-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:14px}.pe-actions button{background:#e5e7eb;color:#111827}.pe-actions .pe-primary{background:var(--pe-accent);color:#fff}
#pe-image-file{display:none}.pe-hidden{display:none!important}.pe-previewing .pe-hover,.pe-previewing .pe-selected{outline:none!important}
@media(max-width:700px){#pe-bar{gap:7px;padding:7px 8px}.pe-help{display:none}#pe-bar button{padding:7px 9px}body.pe-editing{margin-top:44px!important}#pe-panel{top:52px;right:8px;width:calc(100vw - 16px)}}
</style>
<div id="pe-bar" data-pe-ui>
  <strong>Editor do site</strong>
  <span class="pe-help">Texto: clique para editar · Botões/socials: clique para editar destino · Imagens: clique para trocar</span>
  <button id="pe-preview" class="pe-secondary" type="button">Pré-visualizar</button>
  <button id="pe-export" type="button">Exportar página</button>
</div>
<aside id="pe-panel" data-pe-ui aria-label="Propriedades do elemento">
  <header><strong id="pe-panel-title">Propriedades</strong><button id="pe-close" type="button" aria-label="Fechar">×</button></header>
  <form id="pe-form">
    <div id="pe-action-fields">
      <label class="pe-field"><span>Texto do botão/link</span><input id="pe-label" type="text"></label>
      <label class="pe-field"><span>Tipo de ação</span><select id="pe-action-type"><option value="url">URL / página</option><option value="whatsapp">WhatsApp</option><option value="phone">Telefone</option><option value="email">E-mail</option><option value="anchor">Âncora na página</option></select></label>
      <label class="pe-field"><span id="pe-destination-label">Destino</span><input id="pe-destination" type="text" autocomplete="off"></label>
      <label class="pe-field" id="pe-message-wrap"><span>Mensagem pré-preenchida</span><textarea id="pe-message"></textarea></label>
      <label class="pe-field"><span>Nome acessível (aria-label)</span><input id="pe-aria" type="text"></label>
      <label class="pe-check"><input id="pe-new-tab" type="checkbox"><span>Abrir em nova aba</span></label>
      <label class="pe-check"><input id="pe-sync" type="checkbox" checked><span>Atualizar todas as ocorrências deste canal/campo compartilhado</span></label>
      <p class="pe-note" id="pe-field-note">WhatsApp, telefone e redes repetidos podem ser atualizados em navbar, hero, rodapé e CTA flutuante de uma vez.</p>
    </div>
    <div id="pe-image-fields" class="pe-hidden">
      <label class="pe-field"><span>Imagem / URL</span><input id="pe-image-src" type="text" autocomplete="off"></label>
      <label class="pe-field"><span>Texto alternativo</span><input id="pe-image-alt" type="text"></label>
      <button id="pe-choose-image" type="button">Escolher arquivo…</button><input id="pe-image-file" type="file" accept="image/*">
      <label class="pe-check"><input id="pe-image-sync" type="checkbox"><span>Atualizar todas as ocorrências desta mesma imagem</span></label>
      <p class="pe-note">Arquivos locais são incorporados no HTML exportado. Para produção, prefira assets otimizados quando houver pipeline de upload.</p>
    </div>
    <div class="pe-actions"><button id="pe-cancel" type="button">Cancelar</button><button id="pe-apply" class="pe-primary" type="submit">Aplicar</button></div>
  </form>
</aside>
<script id="pe-script">
(function(){
'use strict';

var UI='[data-pe-ui],#pe-style,#pe-script';
var ACTION_SELECTOR='a[href],a[data-href],button[data-href],button[onclick],[role="button"][data-href],[role="button"][onclick],[data-pe-action]';
var IMAGE_SELECTOR='img,[data-pe-bg]';
var state={mode:'edit',selected:null,kind:null,originalHref:'',originalSrc:'',fieldKey:'',sourceType:''};
var $=function(s,r){return(r||document).querySelector(s)};
var $$=function(s,r){return Array.from((r||document).querySelectorAll(s))};

var panel=$('#pe-panel'),form=$('#pe-form'),actionFields=$('#pe-action-fields'),imageFields=$('#pe-image-fields');
var label=$('#pe-label'),type=$('#pe-action-type'),dest=$('#pe-destination'),destLabel=$('#pe-destination-label');
var msg=$('#pe-message'),msgWrap=$('#pe-message-wrap'),aria=$('#pe-aria'),newTab=$('#pe-new-tab'),sync=$('#pe-sync');
var fieldNote=$('#pe-field-note'),imageSrc=$('#pe-image-src'),imageAlt=$('#pe-image-alt'),imageSync=$('#pe-image-sync'),imageFile=$('#pe-image-file');

document.body.classList.add('pe-editing');

function isUI(el){return!!(el&&el.closest&&el.closest(UI))}
function clearSelection(){if(state.selected)state.selected.classList.remove('pe-selected');state.selected=null}
function closePanel(){panel.classList.remove('pe-open');clearSelection()}
function closestAction(target){if(target&&target.closest&&target.closest('[data-pe-no-edit]'))return null;return target&&target.closest?target.closest(ACTION_SELECTOR):null}
function closestImage(target){if(target&&target.closest&&target.closest('[data-pe-no-edit]'))return null;return target&&target.closest?target.closest(IMAGE_SELECTOR):null}

function simpleLabelNode(el){
  if(!el)return null;
  var marked=el.querySelector&&el.querySelector('[data-pe-label]');
  if(marked)return marked;
  if(el.childElementCount===0)return el;
  var candidate=el.querySelector&&el.querySelector('.label,.text,.btn-label,.button-label,span:not([aria-hidden="true"]):not(.icon)');
  if(candidate&&candidate.children.length===0)return candidate;
  return null;
}
function getLabel(el){var n=simpleLabelNode(el);return n?n.textContent.trim():''}
function setLabel(el,v){var n=simpleLabelNode(el);if(n)n.textContent=v}

function extractOnclickHref(code){
  code=code||'';
  var patterns=[
    /window\.open\s*\(\s*['"]([^'"]+)['"]/i,
    /(?:window\.)?location\.href\s*=\s*['"]([^'"]+)['"]/i,
    /(?:window\.)?location\s*=\s*['"]([^'"]+)['"]/i,
    /(?:window\.)?location\.assign\s*\(\s*['"]([^'"]+)['"]/i
  ];
  for(var i=0;i<patterns.length;i++){var m=code.match(patterns[i]);if(m)return m[1]}
  return '';
}
function actionHref(el){
  if(!el)return'';
  return el.getAttribute('href')||el.getAttribute('data-href')||extractOnclickHref(el.getAttribute('onclick')||'')||'';
}
function actionSource(el){
  if(el.hasAttribute('href'))return'href';
  if(el.hasAttribute('data-href'))return'data-href';
  if(el.hasAttribute('onclick')&&extractOnclickHref(el.getAttribute('onclick')))return'onclick';
  return'data-href';
}
function jsQuote(v){return String(v).replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/\r/g,'').replace(/\n/g,'\\n')}
function setActionTarget(el,href,openNew){
  var src=actionSource(el);
  if(el.tagName==='A'||src==='href'){
    el.setAttribute('href',href);
    if(openNew){el.setAttribute('target','_blank');el.setAttribute('rel','noopener noreferrer')}
    else{el.removeAttribute('target');if((el.getAttribute('rel')||'').match(/noopener|noreferrer/))el.removeAttribute('rel')}
    return;
  }
  if(src==='onclick'){
    var safe=jsQuote(href);
    el.setAttribute('onclick',openNew?"window.open('"+safe+"','_blank','noopener');return false;":"window.location.href='"+safe+"';return false;");
    return;
  }
  el.setAttribute('data-href',href);
  if(openNew)el.setAttribute('data-pe-target','_blank');else el.removeAttribute('data-pe-target');
}

function detectAction(h){
  h=(h||'').trim();
  if(/^tel:/i.test(h))return'phone';
  if(/^mailto:/i.test(h))return'email';
  if(/^#/.test(h))return'anchor';
  if(/^(?:https?:\/\/)?(?:wa\.me\/|api\.whatsapp\.com\/|web\.whatsapp\.com\/)|^whatsapp:/i.test(h))return'whatsapp';
  return'url';
}
function parseAction(h,k){
  h=h||'';var o={destination:h,message:''};
  if(k==='phone')o.destination=h.replace(/^tel:/i,'');
  else if(k==='email')o.destination=h.replace(/^mailto:/i,'').split('?')[0];
  else if(k==='anchor')o.destination=h.replace(/^#/,'');
  else if(k==='whatsapp'){
    var m=h.match(/(?:wa\.me\/|phone=)(\+?\d+)/i);o.destination=m?m[1].replace(/\D/g,''):'';
    try{var u=new URL(h,location.href);o.message=u.searchParams.get('text')||''}catch(e){}
  }
  return o;
}
function validUrl(v){
  v=(v||'').trim();
  if(!v)return true;
  if(/^javascript:/i.test(v)||/^vbscript:/i.test(v)||/^data:text\/html/i.test(v))return false;
  return/^(https?:\/\/|\/|\.\/|\.\.\/|#)/i.test(v);
}
function buildHref(k,d,m){
  d=(d||'').trim();
  if(k==='whatsapp'){
    var digits=d.replace(/\D/g,'');
    if(!digits)throw new Error('Informe o número internacional do WhatsApp.');
    return'https://wa.me/'+digits+(m?'?text='+encodeURIComponent(m):'');
  }
  if(k==='phone'){
    var p=d.replace(/[^\d+]/g,'');
    if(!p)throw new Error('Informe o telefone.');
    return'tel:'+p;
  }
  if(k==='email'){
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d))throw new Error('Informe um e-mail válido.');
    return'mailto:'+d;
  }
  if(k==='anchor')return'#'+d.replace(/^#/,'');
  if(!validUrl(d))throw new Error('URL inválida ou esquema não permitido.');
  return d;
}
function inferField(el,h){
  var explicit=el.getAttribute('data-pe-field');
  if(explicit)return explicit;
  h=(h||'').toLowerCase();
  if(detectAction(h)==='whatsapp')return'business.whatsapp';
  if(/^tel:/i.test(h))return'business.phone';
  if(/^mailto:/i.test(h))return'business.email';
  if(/instagram\.com/.test(h))return'business.instagram';
  if(/facebook\.com|fb\.com/.test(h))return'business.facebook';
  if(/tiktok\.com/.test(h))return'business.tiktok';
  if(/youtube\.com|youtu\.be/.test(h))return'business.youtube';
  if(/google\.[^/]+\/maps|maps\.google\./.test(h))return'business.maps';
  return'';
}
function allActions(){return $$(ACTION_SELECTOR).filter(function(el){return!isUI(el)})}
function peersForAction(){
  if(state.fieldKey){
    return allActions().filter(function(el){return inferField(el,actionHref(el))===state.fieldKey});
  }
  return allActions().filter(function(el){return actionHref(el)===state.originalHref});
}
function updateActionFields(){
  var k=type.value;
  msgWrap.classList.toggle('pe-hidden',k!=='whatsapp');
  destLabel.textContent=k==='whatsapp'?'Número internacional (DDI + número)':k==='phone'?'Telefone':k==='email'?'E-mail':k==='anchor'?'ID da seção':'URL / caminho';
}
function openAction(el){
  clearSelection();
  state.selected=el;state.kind='action';state.originalHref=actionHref(el);state.sourceType=actionSource(el);state.fieldKey=inferField(el,state.originalHref);
  el.classList.add('pe-selected');
  $('#pe-panel-title').textContent=state.fieldKey?('Editar '+state.fieldKey.replace('business.','')):'Botão / link';
  actionFields.classList.remove('pe-hidden');imageFields.classList.add('pe-hidden');
  var labelNode=simpleLabelNode(el);
  label.value=labelNode?getLabel(el):'';
  label.disabled=!labelNode;
  label.placeholder=labelNode?'':'Link somente com ícone';
  aria.value=el.getAttribute('aria-label')||'';
  type.value=detectAction(state.originalHref);
  var p=parseAction(state.originalHref,type.value);dest.value=p.destination;msg.value=p.message;
  newTab.checked=el.getAttribute('target')==='_blank'||/window\.open/i.test(el.getAttribute('onclick')||'')||el.getAttribute('data-pe-target')==='_blank';
  sync.checked=true;updateActionFields();
  fieldNote.textContent=state.fieldKey?'Campo compartilhado: '+state.fieldKey+'. Se sincronizar, todas as ocorrências deste canal serão atualizadas.':'Sem campo compartilhado: sincronização usa o mesmo destino atual.';
  panel.classList.add('pe-open');
}

function imgSource(el){return el.tagName==='IMG'?(el.currentSrc||el.getAttribute('src')||''):(el.getAttribute('data-pe-bg-src')||'')}
function peersForImage(){
  if(state.fieldKey)return $$('[data-pe-field="'+CSS.escape(state.fieldKey)+'"]');
  return $$(IMAGE_SELECTOR).filter(function(el){return imgSource(el)===state.originalSrc});
}
function openImage(el){
  clearSelection();state.selected=el;state.kind='image';state.originalSrc=imgSource(el);state.fieldKey=el.getAttribute('data-pe-field')||'';
  el.classList.add('pe-selected');
  $('#pe-panel-title').textContent=el.tagName==='IMG'?'Imagem':'Imagem de fundo';
  actionFields.classList.add('pe-hidden');imageFields.classList.remove('pe-hidden');
  imageSrc.value=state.originalSrc;imageAlt.value=el.tagName==='IMG'?(el.getAttribute('alt')||''):(el.getAttribute('aria-label')||'');
  imageSync.checked=false;panel.classList.add('pe-open');
}
function applyImageTo(el,src,alt){
  if(el.tagName==='IMG'){el.setAttribute('src',src);el.removeAttribute('srcset');if(alt!==undefined)el.setAttribute('alt',alt)}
  else{el.setAttribute('data-pe-bg-src',src);el.style.backgroundImage='url("'+src.replace(/"/g,'%22')+'")';if(alt!==undefined&&alt)el.setAttribute('aria-label',alt)}
}

function bindText(el){
  if(el.dataset.peBoundText||isUI(el)||el.closest('a,button,[role="button"],[data-pe-no-edit]'))return;
  el.dataset.peBoundText='1';
  el.addEventListener('mouseenter',function(){if(state.mode==='edit'&&!el.isContentEditable)el.classList.add('pe-hover')});
  el.addEventListener('mouseleave',function(){el.classList.remove('pe-hover')});
  el.addEventListener('click',function(e){if(state.mode!=='edit')return;e.stopPropagation();el.setAttribute('contenteditable','true');el.classList.remove('pe-hover');el.focus()});
  el.addEventListener('paste',function(e){e.preventDefault();document.execCommand('insertText',false,(e.clipboardData||window.clipboardData).getData('text/plain'))});
  el.addEventListener('blur',function(){el.removeAttribute('contenteditable')});
}
function bindTextAll(){$$('h1,h2,h3,h4,h5,h6,p,li,td,th,figcaption,blockquote').forEach(bindText)}

/* Capture-phase delegation is intentional: it intercepts CTA/social clicks before
   page-specific navigation handlers, SVG child handlers, or stopPropagation logic. */
document.addEventListener('click',function(e){
  if(state.mode!=='edit'||isUI(e.target))return;
  var action=closestAction(e.target);
  if(action){
    e.preventDefault();e.stopPropagation();
    if(e.stopImmediatePropagation)e.stopImmediatePropagation();
    openAction(action);return;
  }
  var image=closestImage(e.target);
  if(image){
    e.preventDefault();e.stopPropagation();
    if(e.stopImmediatePropagation)e.stopImmediatePropagation();
    openImage(image);
  }
},true);

document.addEventListener('pointerover',function(e){
  if(state.mode!=='edit'||isUI(e.target))return;
  var action=closestAction(e.target),image=action?null:closestImage(e.target);
  if(action)action.classList.add('pe-hover');else if(image)image.classList.add('pe-hover');
},true);
document.addEventListener('pointerout',function(e){
  var action=closestAction(e.target),image=action?null:closestImage(e.target);
  if(action)action.classList.remove('pe-hover');else if(image)image.classList.remove('pe-hover');
},true);

type.addEventListener('change',updateActionFields);
form.addEventListener('submit',function(e){
  e.preventDefault();if(!state.selected)return;
  try{
    if(state.kind==='action'){
      var h=buildHref(type.value,dest.value,msg.value);
      var targets=sync.checked?peersForAction():[state.selected];
      targets.forEach(function(el){setActionTarget(el,h,newTab.checked)});
      if(!label.disabled)setLabel(state.selected,label.value);
      if(aria.value)state.selected.setAttribute('aria-label',aria.value);else state.selected.removeAttribute('aria-label');
    }else{
      var src=imageSrc.value.trim();
      if(!src)throw new Error('Informe a imagem.');
      if(/^javascript:/i.test(src)||/^data:text\/html/i.test(src))throw new Error('Origem de imagem inválida.');
      var imgs=imageSync.checked?peersForImage():[state.selected];
      imgs.forEach(function(el){applyImageTo(el,src,imageAlt.value)});
    }
    closePanel();
  }catch(err){alert(err.message||String(err))}
});

$('#pe-close').addEventListener('click',closePanel);
$('#pe-cancel').addEventListener('click',closePanel);
$('#pe-choose-image').addEventListener('click',function(){imageFile.click()});
imageFile.addEventListener('change',function(){
  var f=imageFile.files&&imageFile.files[0];if(!f)return;
  var r=new FileReader();r.onload=function(){imageSrc.value=r.result};r.readAsDataURL(f);imageFile.value='';
});
$('#pe-preview').addEventListener('click',function(){
  state.mode=state.mode==='edit'?'preview':'edit';
  document.body.classList.toggle('pe-previewing',state.mode==='preview');
  this.textContent=state.mode==='preview'?'Voltar a editar':'Pré-visualizar';
  closePanel();
});

function sanitizeRuntimeNode(root){
  var all=Array.from(root.querySelectorAll('*'));
  all.unshift(root);
  all.forEach(function(el){
    if(el.attributes){
      Array.from(el.attributes).forEach(function(attr){
        var n=attr.name.toLowerCase();
        if(n.indexOf('data-darkreader')===0||n==='data-pe-target'||n==='data-pe-bound-text'){
          el.removeAttribute(attr.name);
        }
      });
    }
    if(el.hasAttribute('data-pe-author-style')){
      var authorStyle=el.getAttribute('data-pe-author-style')||'';
      var bgSrc=el.getAttribute('data-pe-bg-src');
      if(bgSrc){
        var decls=authorStyle.split(';').map(function(d){return d.trim()}).filter(Boolean);
        decls=decls.filter(function(d){return d.toLowerCase().indexOf('background-image:')!==0});
        decls.push('background-image: url("'+bgSrc.replace(/"/g,'%22')+'")');
        authorStyle=decls.join('; ')+';';
      }
      if(authorStyle.trim()){
        el.setAttribute('style',authorStyle);
      }else{
        el.removeAttribute('style');
      }
      el.removeAttribute('data-pe-author-style');
    }else{
      var bgSrc=el.getAttribute('data-pe-bg-src');
      if(bgSrc){
        el.setAttribute('style','background-image: url("'+bgSrc.replace(/"/g,'%22')+'");');
      }else{
        el.removeAttribute('style');
      }
    }
    if(el.id==='mainHeader'||el.tagName==='HEADER')el.classList.remove('scrolled');
    if(el.id==='floatingWhatsapp'||el.classList.contains('floating-whatsapp'))el.classList.remove('visible');
    if(el.id==='mobileDrawer'||el.classList.contains('drawer'))el.classList.remove('active');
    if(el.hasAttribute('class')&&!el.getAttribute('class').trim())el.removeAttribute('class');
  });
}
function cleanDocument(){
  try{
    if(window.ScrollTrigger&&typeof window.ScrollTrigger.getAll==='function'){
      window.ScrollTrigger.getAll().forEach(function(st){try{st.revert(true,true)}catch(e){}});
    }
    if(window.gsap&&typeof window.gsap.killTweensOf==='function'){
      try{window.gsap.killTweensOf('*')}catch(e){}
    }
  }catch(e){}
  var doc=document.documentElement.cloneNode(true);
  $$('[data-pe-ui],#pe-style,#pe-script',doc).forEach(function(n){n.remove()});
  $$('[contenteditable]',doc).forEach(function(n){n.removeAttribute('contenteditable')});
  $$('.pe-hover,.pe-selected',doc).forEach(function(n){n.classList.remove('pe-hover','pe-selected')});
  $$('[data-pe-bound-text]',doc).forEach(function(n){n.removeAttribute('data-pe-bound-text')});
  if(doc.querySelector('body'))doc.querySelector('body').classList.remove('pe-editing','pe-previewing');
  sanitizeRuntimeNode(doc);
  try{
    if(window.ScrollTrigger&&typeof window.ScrollTrigger.refresh==='function'){
      setTimeout(function(){try{window.ScrollTrigger.refresh()}catch(e){}},50);
    }
  }catch(e){}
  var html='<!DOCTYPE html>\n'+doc.outerHTML;
  html=html.replace(/<!--\s*PROSPECTOR-(?:EDITOR|PUBLISH)-(?:START|END)\s*-->/gi,'');
  return html;
}
window.cleanDocument = cleanDocument;
window.cleanPublicDocument = cleanDocument;
$('#pe-export').addEventListener('click',function(){
  var blob=new Blob([cleanDocument()],{type:'text/html;charset=utf-8'}),a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download=(document.documentElement.getAttribute('data-pe-export-name')||'index.html');a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href)},1000);
});

bindTextAll();
new MutationObserver(function(){bindTextAll()}).observe(document.body,{childList:true,subtree:true});
})();
</script>
<!-- PROSPECTOR-EDITOR-END -->'''


def tag_author_styles(html_text: str) -> str:
    html_text = re.sub(r'\s+data-pe-author-style="[^"]*"', '', html_text)

    def _repl(m):
        tag = m.group(1)
        attrs_before = m.group(2)
        quote = m.group(3)
        style_val = m.group(4)
        attrs_after = m.group(5)
        escaped_style = html_lib.escape(style_val, quote=True)
        return f'<{tag}{attrs_before} data-pe-author-style="{escaped_style}" style={quote}{style_val}{quote}{attrs_after}>'

    pattern = re.compile(r'<([a-zA-Z0-9\-]+)([^>]*?)\sstyle=(["\'])(.*?)\3([^>]*?)>', re.DOTALL | re.IGNORECASE)
    return pattern.sub(_repl, html_text)


def strip_existing_editor(html: str) -> str:
    return re.compile(re.escape(START) + r".*?" + re.escape(END), re.S).sub("", html)


def infer_output(source: pathlib.Path) -> pathlib.Path:
    if source.stem.endswith("-editor"):
        return source
    return source.with_name(source.stem + "-editor" + source.suffix)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Prospector client visual editor")
    parser.add_argument("html", help="Source static HTML file")
    parser.add_argument("--output", "-o", help="Editor output path (default: <source>-editor.html)")
    args = parser.parse_args()

    source = pathlib.Path(args.html)
    if not source.exists():
        raise SystemExit(f"Source not found: {source}")

    output = pathlib.Path(args.output) if args.output else infer_output(source)
    html = strip_existing_editor(source.read_text(encoding="utf-8"))
    if "</body>" not in html.lower():
        raise SystemExit("Source HTML has no </body> tag")

    html = tag_author_styles(html)
    idx = html.lower().rfind("</body>")
    out = html[:idx] + EDITOR_LAYER + "\n" + html[idx:]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(out, encoding="utf-8")
    print(f"Editor visual gerado em: {output}")


if __name__ == "__main__":
    main()
