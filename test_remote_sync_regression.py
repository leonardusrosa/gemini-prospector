#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for local-only Prospector CRM publication.

Architecture: local SQLite is the ONLY CRM source of truth. Phoenix remote
sync (prospector_remote) is a legacy/optional adapter and must never run
during normal publication.
"""

import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import prospector_remote


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


def _load_mcp(db_path):
    spec = importlib.util.spec_from_file_location('prospector_mcp_test', 'prospector-mcp.py')
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    pm.DB = db_path
    return pm


def _make_db(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('''CREATE TABLE leads (slug TEXT PRIMARY KEY, nome TEXT, nicho TEXT, cidade TEXT, nota REAL,
        avaliacoes INTEGER, email TEXT, telefone TEXT, whatsapp TEXT, siteAntigo TEXT, motivo TEXT,
        status TEXT, urlNova TEXT, dataProposta TEXT, valor REAL, obs TEXT, contratoStatus TEXT,
        contratoEm TEXT, manutencao REAL, pago INTEGER, docCliente TEXT, endCliente TEXT,
        websiteStatus TEXT, siteMode TEXT, country TEXT, locale TEXT, language TEXT,
        phoneCountryCode TEXT, atualizado TEXT)''')
    c.execute(
        'INSERT INTO leads (slug, nome, status, nota, avaliacoes, urlNova, endCliente, telefone, whatsapp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        ('clinica-teste-sync', 'Clinica Teste Sync', 'qualified', 4.2, 5,
         'https://prospector-sites-beta.vercel.app/clientes/clinica-teste-sync/',
         'Av. Principal, 100 - Centro, Rio Claro - SP',
         '(19) 99999-8888', '5519999998888'))
    conn.commit()
    conn.close()


class TestLocalPublication(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, 'test_prospector.db')
        _make_db(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_publication_updates_local_db_without_remote(self):
        pm = _load_mcp(self.db_path)
        with patch('urllib.request.urlopen') as mock_urlopen:
            res = pm.f_status('clinica-teste-sync', 'publicado')
            self.assertTrue(res['ok'])
            self.assertEqual(res['status_result'], 'PUBLISHED_LOCAL_ONLY')
            self.assertNotIn('remote_sync', res)
            mock_urlopen.assert_not_called()
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT status FROM leads WHERE slug='clinica-teste-sync'").fetchone()
        conn.close()
        self.assertEqual(row[0], 'publicado')

    def test_salvar_publicado_updates_local_db_without_remote(self):
        pm = _load_mcp(self.db_path)
        with patch('urllib.request.urlopen') as mock_urlopen:
            res = pm.f_salvar({'slug': 'clinica-teste-sync', 'status': 'publicado'})
            self.assertTrue(res['ok'])
            self.assertEqual(res['status_result'], 'PUBLISHED_LOCAL_ONLY')
            self.assertNotIn('remote_sync', res)
            mock_urlopen.assert_not_called()

    def test_credentials_never_leak_in_redact(self):
        secret = 'SUPER_SECRET_TOKEN_999888'
        with patch.dict(os.environ, {'PROSPECTOR_AUTH_PASSWORD': secret, 'PROSPECTOR_AUTH_USER': 'admin'}):
            raw_text = 'Error with password ' + secret
            cleaned = prospector_remote.redact(raw_text)
            self.assertNotIn(secret, cleaned)
            self.assertIn('[REDACTED]', cleaned)


class TestLegacyRemoteAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, 'test_prospector.db')
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE leads (slug TEXT PRIMARY KEY, status TEXT, nota REAL, avaliacoes INTEGER, urlNova TEXT, endCliente TEXT, telefone TEXT, whatsapp TEXT)')
        c.execute(
            'INSERT INTO leads (slug, status, nota, avaliacoes, urlNova, endCliente, telefone, whatsapp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            ('clinica-teste-sync', 'publicado', 4.2, 5,
             'https://prospector-sites-beta.vercel.app/clientes/clinica-teste-sync/',
             'Av. Principal, 100 - Centro, Rio Claro - SP',
             '(19) 99999-8888', '5519999998888'))
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmp_dir.cleanup()

    @patch('urllib.request.urlopen')
    def test_legacy_sync_success_and_readback(self, mock_urlopen):
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
        res = prospector_remote.sync_lead(
            'clinica-teste-sync',
            db_path=self.db_path,
            base_url='https://mock.prospector.test',
            user='mockuser',
            password='mockpassword'
        )
        self.assertTrue(res['ok'])
        self.assertEqual(res['sync_status'], 'REMOTE_SYNC_OK')
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch('urllib.request.urlopen')
    def test_legacy_field_divergence_surfaced(self, mock_urlopen):
        divergent_lead = {
            'slug': 'clinica-teste-sync',
            'status': 'published',
            'nota': 4.8,
            'avaliacoes': 28,
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
        self.assertIn('divergences', res)
        self.assertIn('nota', res['divergences'])
        self.assertIn('avaliacoes', res['divergences'])


if __name__ == '__main__':
    unittest.main()
