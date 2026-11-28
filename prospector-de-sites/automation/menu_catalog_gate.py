"""Source-grounded ON-PAGE restaurant menu gate.

A verified menu must be represented by real, editable HTML cards on the
restaurant landing page. External ordering and official-menu links may
coexist but cannot stand in for the on-page catalog.
"""
from __future__ import annotations
import hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path

SHA=re.compile(r"^[0-9a-f]{64}$")
ID=re.compile(r"^[a-zA-Z][a-zA-Z0-9_:.-]{0,119}$")
MENU_NICHES={"restaurant","pizzeria","cafe"}
COLLECTION_KINDS={"menu","pricing"}

def sha_file(path:Path)->str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(s:str)->str:
    return re.sub(r"\s+"," ",s or "").strip().casefold()

class Node:
    def __init__(self,tag,attrs,parent):
        self.tag=tag
        self.attrs=dict(attrs)
        self.parent=parent
        self.children=[]
        self.text=""

class MenuParser(HTMLParser):
    def __init__(self,html:str):
        super().__init__(convert_charrefs=True)
        self.root=Node("root",[],None)
        self.stack=[self.root]
        self.nodes=[]
        self.by_id={}
        self.feed(html)
    def handle_starttag(self,tag,attrs):
        node=Node(tag,attrs,self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if node.attrs.get("id"):
            self.by_id.setdefault(node.attrs["id"],[]).append(node)
        if tag not in ("img","input","meta","link","br","hr","area","source","wbr"):
            self.stack.append(node)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:]
                return
    def handle_data(self,data):
        for node in self.stack:
            node.text+=data
    def unique(self,ident):
        hits=self.by_id.get(ident,[])
        if len(hits)!=1:
            raise ValueError("Menu ID missing or duplicated: "+ident)
        return hits[0]

def inside(node,ancestor):
    while node is not None:
        if node is ancestor:return True
        node=node.parent
    return False

def validate_menu_catalog(plan:dict,html:str,lead_slug:str,
                          research:dict|None=None)->dict:
    if plan.get("schemaVersion")!=1 or plan.get("leadSlug")!=lead_slug:
        raise ValueError("Menu plan schema/identity mismatch")
    if plan.get("verifiedMenu") is not True or plan.get("fullMenuCaptured") is not True:
        raise ValueError("Menu needs independently verified complete source inventory")
    if plan.get("noOutbound") is not True or plan.get("publicReleaseAuthorized") is not False:
        raise ValueError("Menu plans cannot enable outreach/public launch")
    evidence=plan.get("sourceEvidence")
    if not isinstance(evidence,dict) or not re.fullmatch(r"https://[^\s]+",str(evidence.get("sourcePage") or "")):
        raise ValueError("Official menu source URL missing")
    try:
        path=Path(evidence["path"])
        digest=evidence["sha256"]
    except (KeyError,TypeError) as err:
        raise ValueError("Source menu screenshot proof missing") from err
    if (not path.is_file() or not isinstance(digest,str) or not SHA.fullmatch(digest)
            or sha_file(path)!=digest):
        raise ValueError("Menu source screenshot changed or missing")
    if research and (research.get("leadSlug")!=lead_slug or research.get("noOutbound") is not True):
        raise ValueError("Menu and frozen research lead mismatch")
    parser=MenuParser(html)
    section=parser.unique("menu")
    if section.tag!="section":
        raise ValueError("Menu needs semantic on-page section#menu")
    items=plan.get("items")
    if not isinstance(items,list) or not 1<=len(items)<=120:
        raise ValueError("Full menu requires 1-120 source-reviewed items")
    ids=set()
    categories=set()
    containers=set()
    for item in items:
        if not isinstance(item,dict):
            raise ValueError("Invalid menu source item")
        ident,title,category=item.get("id"),item.get("title"),item.get("category")
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident in ids:
            raise ValueError("Menu item ID invalid or duplicate")
        if not isinstance(title,str) or len(title.strip())<2:
            raise ValueError("Menu item name missing")
        if not isinstance(category,str) or len(category.strip())<3:
            raise ValueError("Menu category missing")
        ids.add(ident)
        categories.add(norm(category))
        node=parser.unique(ident)
        if not inside(node,section) or node.tag not in ("article","li","div"):
            raise ValueError("Menu item must be visible on page inside menu section")
        if "data-pe-item" not in node.attrs:
            raise ValueError("Menu item must remain individually CMS editable")
        if norm(title) not in norm(node.text):
            raise ValueError("Verified menu item name missing: "+ident)
        if item.get("description") is not None:
            desc=item.get("description")
            if not isinstance(desc,str) or norm(desc) not in norm(node.text):
                raise ValueError("Source-reviewed description missing: "+ident)
        price=item.get("price")
        if price is not None:
            if not isinstance(price,str) or not re.search(re.escape(norm(price))+r"(?![0-9.,])", norm(node.text)):
                raise ValueError("Verified menu price missing: "+ident)
        elif item.get("priceNotPublished") is not True:
            raise ValueError("Unknown price must be explicitly flagged, not fabricated")
        container=node.parent
        if not container or container.attrs.get("data-pe-collection") not in COLLECTION_KINDS or not inside(container,section):
            raise ValueError("Menu cards must be direct children of CMS collections")
        containers.add(id(container))
    headings=[norm(el.text) for el in parser.nodes if el.tag in ("h2","h3","h4") and inside(el,section)]
    for cat in categories:
        if not any(cat in heading for heading in headings):
            raise ValueError("Missing on-page menu category heading: "+cat)
    for el in parser.nodes:
        if (inside(el,section) and el.tag in ("article","li") and
                "data-pe-item" in el.attrs and el.attrs.get("id") not in ids):
            raise ValueError("Unreviewed menu card exists on page")
    if plan.get("ownerCanEditPrices") is not True:
        raise ValueError("Menus must support Client CMS editing of prices and items")
    return {"result":"ON_PAGE_MENU_PASS","verifiedItems":len(items),
            "categories":len(categories),"cmsCollections":len(containers),
            "outboundMenuRedirectNotSubstitute":True,
            "productionReleaseAuthorized":False}

def audit_file(html:Path,plan:Path,slug:str,research:dict|None=None)->dict:
    return validate_menu_catalog(json.loads(Path(plan).read_text(encoding="utf-8")),
                                 Path(html).read_text(encoding="utf-8"),slug,research)
