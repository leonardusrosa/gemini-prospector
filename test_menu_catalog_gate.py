"""Source-verifiable on-page menu regression tests (no internet/provider calls)."""
from __future__ import annotations
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"prospector-de-sites"/"automation"))
import menu_catalog_gate as gate
import site_review_rounds as rounds

HTML='''<!doctype html><html lang="en"><head><title>Synthetic Pizzeria</title></head>
<body><h1>Fictional Pizzeria</h1><section id="menu">
<h2>Our complete menu</h2><h3>Feral pizzas</h3>
<div id="menu-grid" data-pe-collection="menu">
<article id="pizza-one" data-pe-item><h4>Pizza One</h4><p>Cheese and basil</p><b>$12</b></article>
<article id="pizza-two" data-pe-item><h4>Pizza Two</h4><p>Tomato and ricotta</p><b>$16</b></article></div>
<h3>Sides</h3><div data-pe-collection="menu" id="sides">
<article data-pe-item id="ranch"><h4>Ranch</h4><p>Scratch-made ranch</p><b>$1</b></article>
</div>
<a href="https://example.org/order" target="_blank">Order with restaurant</a></section>
</body></html>'''

class MenuCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.screen=self.folder/"source-menu.png"
        self.screen.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic screenshot placeholder only")
        self.plan={
            "schemaVersion":1,"leadSlug":"fictional-pizzeria","noOutbound":True,
            "publicReleaseAuthorized":False,"verifiedMenu":True,
            "fullMenuCaptured":True,"ownerCanEditPrices":True,
            "sourceEvidence":{
                "sourcePage":"https://example.org/official-menu",
                "path":str(self.screen),"sha256":gate.sha_file(self.screen),
            },
            "items":[
                {"id":"pizza-one","title":"Pizza One","description":"Cheese and basil","price":"$12","category":"Feral pizzas"},
                {"id":"pizza-two","title":"Pizza Two","description":"Tomato and ricotta","price":"$16","category":"Feral pizzas"},
                {"id":"ranch","title":"Ranch","description":"Scratch-made ranch","price":"$1","category":"Sides"},
            ]
        }
        self.research={"leadSlug":"fictional-pizzeria","noOutbound":True}

    def gate(self,html=HTML):
        return gate.validate_menu_catalog(self.plan,html,"fictional-pizzeria",self.research)

    def test_on_page_complete_catalog_passes_with_separate_order_button(self):
        r=self.gate()
        self.assertEqual(r["result"],"ON_PAGE_MENU_PASS")
        self.assertEqual(r["verifiedItems"],3)
        self.assertEqual(r["categories"],2)
        self.assertEqual(r["cmsCollections"],2)

    def test_external_order_link_not_substitute_for_inline_menu(self):
        bad='<!doctype html><html><body><h1>Pizzeria</h1><section id="menu">'+(
            '<h2>Menu</h2><a href="https://example.org/menu">See our menu</a></section></body></html>')
        with self.assertRaisesRegex(ValueError,"Menu ID"):
            self.gate(bad)

    def test_wrong_price_rejected(self):
        with self.assertRaisesRegex(ValueError,"price"):
            self.gate(HTML.replace("<b>$16</b>","<b>$160</b>"))

    def test_wrong_description_rejected(self):
        with self.assertRaisesRegex(ValueError,"description"):
            self.gate(HTML.replace("Tomato and ricotta","Ham and cheese"))

    def test_card_outside_menu_rejected(self):
        text=HTML.replace('</article></div>\n<h3>Sides', '</article></div>\n<h3>Sides')
        # Remove the semantic menu section entirely, preserving cards elsewhere.
        text=text.replace('<section id="menu">','<section id="products">')
        with self.assertRaisesRegex(ValueError,"Menu ID"):
            self.gate(text)

    def test_client_cms_direct_child_required(self):
        with self.assertRaisesRegex(ValueError,"CMS editable"):
            self.gate(HTML.replace('id="pizza-two" data-pe-item','id="pizza-two"'))

    def test_fabricated_unreviewed_item_rejected(self):
        bad=HTML.replace('</article></div>\n<h3>Sides', '''</article>
        <article id="fake-pizza" data-pe-item><h4>Invented Product</h4></article>
        </div><h3>Sides''')
        with self.assertRaisesRegex(ValueError,"Unreviewed"):
            self.gate(bad)

    def test_no_real_price_must_be_declared(self):
        self.plan["items"][0]["price"]=None
        with self.assertRaisesRegex(ValueError,"explicitly flagged"):
            self.gate()

    def test_price_not_published_is_allowed_not_invented(self):
        self.plan["items"][0]["price"]=None
        self.plan["items"][0]["priceNotPublished"]=True
        self.assertEqual(self.gate()["result"],"ON_PAGE_MENU_PASS")

    def test_stale_first_party_screenshot_rejected(self):
        self.screen.write_bytes(b"tampered evidence")
        with self.assertRaisesRegex(ValueError,"changed or missing"):
            self.gate()

    def test_missing_catalog_category_heading_rejected(self):
        with self.assertRaisesRegex(ValueError,"category heading"):
            self.gate(HTML.replace('<h3>Sides</h3>','<p>Sides available</p>'))

    def test_draft_without_complete_menu_flag_rejected(self):
        self.plan["fullMenuCaptured"]=False
        with self.assertRaisesRegex(ValueError,"complete source"):
            self.gate()

    def test_owner_must_be_able_to_edit_item_prices(self):
        self.plan["ownerCanEditPrices"]=False
        with self.assertRaisesRegex(ValueError,"editing"):
            self.gate()

    def test_menu_research_stage_requires_source_and_classification(self):
        with tempfile.TemporaryDirectory() as td:
            here=Path(td)
            manifest=here/"research.json"
            manifest.write_text(json.dumps({
                "schemaVersion":1,"leadSlug":"fictional-pizzeria",
                "country":"US","noOutbound":True,"mode":"READ_ONLY_RESEARCH",
                "assessment":{"scope":"ALLOW","priorityNiche":"pizzeria"},
                "assets":[],"socialProfiles":[],"researchChecks":{},
            }))
            run=rounds.new_run(manifest)
            stage=here/"stage.json"
            stage.write_text(json.dumps({
                "schemaVersion":1,"stage":"FACTS_AND_IDENTITIES",
                "sourceManifestSha256":run["sourceManifestSha256"],
            }))
            with self.assertRaisesRegex(ValueError,"classify menu presence"):
                rounds.submit_artifact(run,"FACTS_AND_IDENTITIES",stage,"facts-generator")

if __name__=="__main__":
    unittest.main(verbosity=2)
