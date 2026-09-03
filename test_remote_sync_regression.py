#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for Prospector CRM production synchronization and secret hardening."""

import io
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import prospector_remote
# prospector_mcp loaded dynamically in tests


class DummyHTTPResponse:
    def __init__(self, status, payload):
        self.status = status
        self._raw = json.dumps(payload).encode('utf-8')

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestProspectorRemoteSync(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, 'test_prospector.db')
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE leads (
                slug TEXT PRIMARY KEY,
                nome TEXT,
                nicho TEXT,
                cidade TEXT,
                nota REAL,
                avaliacoes INTEGER,
                email TEXT,
                telefone TEXT,
                whatsapp TEXT,
                siteAntigo TEXT,
                motivo TEXT,
                status TEXT,
                urlNova TEXT,
                dataProposta TEXT,
                valor REAL,
                obs TEXT,
                contratoStatus TEXT,
                contratoEm TEXT,
                manutencao REAL,
                pago INTEGER,
                docCliente TEXT,
                endCliente TEXT,
                atualizado TEXT,
                placeId TEXT,
                opportunityType TEXT,
                opportunityScore INTEGER,
                classificationEvidence TEXT,
                mainRisk TEXT,
                factualContent TEXT,
                imageryLevel TEXT,
                socialUrls TEXT,
                mapsUrl TEXT,
                runId INTEGER,
                criadoEm TEXT,
                country TEXT,
                locale TEXT,
                language TEXT,
                phoneCountryCode TEXT,
                websiteStatus TEXT,
                siteMode TEXT
            )
        ''')
        c.execute('''
            INSERT INTO leads (slug, nome, status, nota, avaliacoes, urlNova, endCliente, telefone, whatsapp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'clinica-teste-sync',
            'Clínica Teste Sync',
            'qualified',
            4.2,
            5,
            'https://prospector-sites-beta.vercel.app/clientes/clinica-teste-sync/',
            'Av. Principal, 100 - Centro, Rio Claro - SP',
            '(19) 99999-8888',
            '5519999998888'
        ))
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch('urllib.request.urlopen')
    def test_sync_success_and_readback_verification(self, mock_urlopen):
        # 1st call: PUT -> 200 ok
        # 2nd call: GET -> returns matching lead
        remote_lead = {
            'slug': 'clinica-teste-sync',
            'status': 'published',
            'nota': 4.2,
            'avaliacoes': 5,
            'urlNova': 'https://prospector-sites-beta.vercel.app/clientes/clinica-teste-sync/',
            'endCliente': 'Av. Principal, 100 - Centro, Rio Claro - SP',
            'telefone': '19999998888',
            'whatsapp': '5519999998888'
        }
        mock_urlopen.side_effect = [
            DummyHTTPResponse(200, {'ok': True}),
            DummyHTTPResponse(200, [remote_lead])
        ]

        # Update local status to publicado
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE leads SET status='publicado' WHERE slug='clinica-teste-sync'")
        conn.commit()
        conn.close()

        res = prospector_remote.sync_lead(
            'clinica-teste-sync',
            db_path=self.db_path,
            base_url='https://mock.prospector.test',
            user='mockuser',
            password='mockpassword'
        )

        self.assertTrue(res['ok'])
        self.assertEqual(res['sync_status'], 'REMOTE_SYNC_OK')
        self.assertEqual(res['status_result'], 'PUBLISHED + REMOTE_SYNC_OK')
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch('urllib.request.urlopen')
    def test_remote_failure_surfaced_and_blocks_full_success(self, mock_urlopen):
        import urllib.error
        # Mock network error or HTTP 500
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'https://mock.prospector.test/api/leads/clinica-teste-sync',
            500, 'Internal Server Error', {}, io.BytesIO(b'{"error": "Database down"}')
        )

        res = prospector_remote.sync_lead(
            'clinica-teste-sync',
            db_path=self.db_path,
            base_url='https://mock.prospector.test',
            user='mockuser',
            password='mockpassword'
        )

        self.assertFalse(res['ok'])
        self.assertEqual(res['sync_status'], 'REMOTE_SYNC_FAILED')
        self.assertEqual(res['status_result'], 'REMOTE_SYNC_PENDING')
        self.assertIn('Remote PUT failed', res['error'])

    @patch('urllib.request.urlopen')
    def test_field_divergence_surfaced_on_readback(self, mock_urlopen):
        # PUT succeeds, but GET readback returns stale rating 4.8 instead of 4.2
        divergent_lead = {
            'slug': 'clinica-teste-sync',
            'status': 'published',
            'nota': 4.8,  # Stale!
            'avaliacoes': 28,  # Stale!
            'urlNova': 'https://prospector-sites-beta.vercel.app/clientes/clinica-teste-sync/',
            'endCliente': 'Av. Principal, 100 - Centro, Rio Claro - SP',
            'telefone': '19999998888',
            'whatsapp': '5519999998888'
        }
        mock_urlopen.side_effect = [
            DummyHTTPResponse(200, {'ok': True}),
            DummyHTTPResponse(200, [divergent_lead])
        ]

        res = prospector_remote.sync_lead(
            'clinica-teste-sync',
            db_path=self.db_path,
            base_url='https://mock.prospector.test',
            user='mockuser',
            password='mockpassword'
        )

        self.assertFalse(res['ok'])
        self.assertEqual(res['sync_status'], 'REMOTE_SYNC_FAILED')
        self.assertEqual(res['status_result'], 'REMOTE_SYNC_PENDING')
        self.assertIn('divergences', res)
        self.assertIn('nota', res['divergences'])
        self.assertIn('avaliacoes', res['divergences'])

    def test_credentials_never_leak_in_redact(self):
        secret = 'SUPER_SECRET_TOKEN_999888'
        with patch.dict(os.environ, {'PROSPECTOR_AUTH_PASSWORD': secret, 'PROSPECTOR_AUTH_USER': 'admin'}):
            raw_text = f"Error communicating with Basic YWRtaW46U1VQRVJfU0VDUkVUX1RPS0VOXzk5OTg4OA== using password {secret}"
            cleaned = prospector_remote.redact(raw_text)
            self.assertNotIn(secret, cleaned)
            self.assertIn('[REDACTED]', cleaned)

    @patch('prospector_remote.sync_lead')
    def test_mcp_f_status_publication_workflow(self, mock_sync):
        import importlib.util
        spec = importlib.util.spec_from_file_location('prospector_mcp_test', 'prospector-mcp.py')
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = self.db_path

        # Case 1: Remote sync succeeds
        mock_sync.return_value = {
            'ok': True,
            'sync_status': 'REMOTE_SYNC_OK',
            'status_result': 'PUBLISHED + REMOTE_SYNC_OK'
        }
        res_ok = pm.f_status('clinica-teste-sync', 'publicado')
        self.assertTrue(res_ok['ok'])
        self.assertEqual(res_ok['remote_sync'], 'REMOTE_SYNC_OK')
        self.assertEqual(res_ok['status_result'], 'PUBLISHED + REMOTE_SYNC_OK')

        # Case 2: Remote sync fails -> local updated, but publication fails closed
        mock_sync.return_value = {
            'ok': False,
            'sync_status': 'REMOTE_SYNC_FAILED',
            'status_result': 'REMOTE_SYNC_PENDING',
            'error': 'Network timeout to Phoenix VPS'
        }
        res_fail = pm.f_status('clinica-teste-sync', 'publicado')
        self.assertFalse(res_fail['ok'])
        self.assertEqual(res_fail['remote_sync'], 'REMOTE_SYNC_FAILED')
        self.assertEqual(res_fail['status_result'], 'REMOTE_SYNC_PENDING')
        self.assertIn('Network timeout', res_fail['error'])


if __name__ == '__main__':
    unittest.main()
