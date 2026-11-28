import base64,copy,unittest,os
from datetime import datetime,timezone,timedelta
import test_hero_motion as fixtures
from hero_owner_review import receipt_payload,verify_receipt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from unittest.mock import patch

class OwnerReceiptTests(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate()
        self.pub=self.key.public_key().public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo)
        self.plan={"leadSlug":"fixture","_fileSha256":"a"*64,"sourceManifestSha256":"b"*64}
        self.delivery={"_fileSha256":"c"*64,"generatorId":"worker"}
        self.qa={"_fileSha256":"d"*64}
        self.receipt={"schemaVersion":2,"decision":"APPROVED","channel":"authenticated_admin_review",
                      "actorType":"human","autoSelected":False,"leadSlug":"fixture",
                      "planSha256":"a"*64,"sourceManifestSha256":"b"*64,"deliverySha256":"c"*64,
                      "qaSha256":"d"*64,"reviewBundleSha256":"e"*64,"approverId":"owner",
                      "issuedAt":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        self.sign(self.receipt)
    def sign(self,receipt):
        receipt["signature"]=base64.b64encode(self.key.sign(receipt_payload(receipt))).decode()
    def verify(self,r):
        return verify_receipt(self.plan,self.delivery,self.qa,r,public_key=self.pub,owner_id="owner")
    def test_valid_owner(self):
        self.assertEqual(self.verify(self.receipt),"owner")
    def test_every_artifact_bound(self):
        for field in ("leadSlug","planSha256","deliverySha256","qaSha256","sourceManifestSha256","reviewBundleSha256"):
            r=copy.deepcopy(self.receipt);r[field]="f"*64
            with self.assertRaises(ValueError):self.verify(r)
    def test_wrong_key_and_generator_rejected(self):
        other=Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo)
        with self.assertRaises(ValueError):
            verify_receipt(self.plan,self.delivery,self.qa,self.receipt,public_key=other,owner_id="owner")
        self.delivery["generatorId"]="owner"
        with self.assertRaises(ValueError):self.verify(self.receipt)
    def test_rejection_and_expiry(self):
        for field,value in (("decision","REJECTED"),("issuedAt",(datetime.now(timezone.utc)-timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ"))):
            r=copy.deepcopy(self.receipt);r[field]=value;self.sign(r)
            with self.assertRaises(ValueError):self.verify(r)
    def test_legacy_receipt_cannot_authorize_storyboard(self):
        with patch.object(fixtures.hero,"validate_delivery"),patch.object(fixtures.hero,"is_storyboard",return_value=True):
            with self.assertRaisesRegex(ValueError,"Explicit owner approval"):
                fixtures.hero.approve_with_human_receipt(self.plan,self.delivery,self.qa,{"schemaVersion":1})
