#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de importação dos resultados de Rio Claro e bateria completa de testes de discovery CRM.
"""
import os
import sqlite3
import json
import discovery_service

PASTA = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA, 'prospector.db')

def run_tests_and_import():
    conn = sqlite3.connect(DB_PATH)
    discovery_service.setup_db(conn)

    print("=== TESTE 1: Registro de Discovery Run ===")
    run_id = discovery_service.registrar_run(conn, {
        'query': 'dentistas clinicas odontologicas Rio Claro SP',
        'nicho': 'dentistas / clínicas odontológicas',
        'location': 'Rio Claro, SP',
        'country': 'BR',
        'locale': 'pt-BR',
        'totalAnalyzed': 14,
        'countExistingWeak': 2,
        'countNone': 4,
        'countHealthy': 6,
        'countUnknown': 2,
        'countInsufficient': 0,
        'metadata': {'scanSource': 'Google Maps + Web Search + Browser Verification'}
    })
    print(f"Run registrado com ID: {run_id}")
    assert run_id > 0, "Run ID deve ser maior que 0"

    print("\n=== TESTE 2: Importação dos Leads com Upsert e Deduplicação ===")
    leads_import = [
        {
            'slug': 'instituto-ferreira-odontologia-rio-claro',
            'placeId': 'ChIJ_instituto_ferreira_rc',
            'nome': 'Instituto Ferreira Odontologia e Harmonização Orofacial',
            'nicho': 'Odontologia e Harmonização Orofacial',
            'cidade': 'Rio Claro, SP',
            'country': 'BR',
            'locale': 'pt-BR',
            'language': 'pt',
            'phoneCountryCode': '55',
            'nota': 4.9,
            'avaliacoes': 45,
            'telefone': '(19) 3534-6554',
            'whatsapp': '5519997491316',
            'email': 'webmaster@clinicaferreira.com.br',
            'endCliente': 'Rua 5, 3379 (entre Avs. 46 e 50), Jardim Portugal, Rio Claro - SP',
            'siteAntigo': 'https://www.institutoferreira.com.br',
            'websiteStatus': 'existing_weak',
            'siteMode': 'redesign',
            'opportunityType': 'REDESIGN',
            'opportunityScore': 88,
            'classificationEvidence': 'Site ativo sobre tema antigo WordPress (Twenty Seventeen) com galeria FooGallery em miniaturas 150x150 e links antigos para www2.clinicaferreira.com.br.',
            'mainRisk': 'Volume de avaliações oscila entre nomes legados (Clínica Ferreira vs Instituto Ferreira).',
            'factualContent': 'High',
            'imageryLevel': 'High',
            'status': 'qualified'
        },
        {
            'slug': 'mb-odontologia-premium-rio-claro',
            'placeId': 'ChIJ_mb_odontologia_rc',
            'nome': 'MB Odontologia Premium',
            'nicho': 'Implantodontia e Reabilitação Oral',
            'cidade': 'Rio Claro, SP',
            'country': 'BR',
            'locale': 'pt-BR',
            'language': 'pt',
            'phoneCountryCode': '55',
            'nota': 4.8,
            'avaliacoes': 30,
            'telefone': '(19) 3524-7817',
            'whatsapp': '551935247817',
            'email': None,
            'endCliente': 'Rua 15, Consolação, Rio Claro - SP',
            'siteAntigo': 'https://www.mbodontologiapremium.com.br',
            'websiteStatus': 'existing_weak',
            'siteMode': 'redesign',
            'opportunityType': 'REDESIGN',
            'opportunityScore': 79,
            'classificationEvidence': 'Landing page criada em builder genérico (GreatPages) com estrutura engessada, ícones genéricos e contraste agressivo.',
            'mainRisk': 'Confirmar se telefone cadastrado é WhatsApp direto ou fixo.',
            'factualContent': 'Medium',
            'imageryLevel': 'Medium',
            'status': 'qualified'
        },
        {
            'slug': 'iost-ortodontia-aline-iost-rio-claro',
            'placeId': 'ChIJ_iost_ortodontia_rc',
            'nome': 'IOST Ortodontia - Dra. Aline Iost',
            'nicho': 'Ortodontia e Ortopedia Facial',
            'cidade': 'Rio Claro, SP',
            'country': 'BR',
            'locale': 'pt-BR',
            'language': 'pt',
            'phoneCountryCode': '55',
            'nota': 5.0,
            'avaliacoes': 42,
            'telefone': '(19) 3534-0000',
            'whatsapp': '5519996610000',
            'email': None,
            'endCliente': 'Avenida 9, nº 411, Sala 03, Bairro Saúde, Rio Claro - SP',
            'siteAntigo': None,
            'websiteStatus': 'none',
            'siteMode': 'new_site_concept',
            'opportunityType': 'NOVO SITE',
            'opportunityScore': 84,
            'classificationEvidence': 'Profissional especialista (USP Bauru, Invisalign Doctor) com consultório ativo sem site oficial próprio após verificação em múltiplas fontes.',
            'mainRisk': 'Fotos do espaço interno dependem de coleta de perfis ou envio pelo cliente.',
            'factualContent': 'Medium',
            'imageryLevel': 'Medium',
            'status': 'qualified'
        },
        {
            'slug': 'clinica-prado-odontologia-rio-claro',
            'placeId': 'ChIJ_clinica_prado_rc',
            'nome': 'Clínica Prado - Odontologia e Estética',
            'nicho': 'Odontologia Geral e Estética',
            'cidade': 'Rio Claro, SP',
            'country': 'BR',
            'locale': 'pt-BR',
            'language': 'pt',
            'phoneCountryCode': '55',
            'nota': 4.9,
            'avaliacoes': 35,
            'telefone': '(19) 99978-7182',
            'whatsapp': '5519999787182',
            'email': None,
            'endCliente': 'Rua 3, nº 107, Bairro Saúde / Centro, Rio Claro - SP',
            'siteAntigo': None,
            'websiteStatus': 'none',
            'siteMode': 'new_site_concept',
            'opportunityType': 'NOVO SITE',
            'opportunityScore': 80,
            'classificationEvidence': 'Empresa ativa constituída em 2021 com localização física no bairro Saúde e zero website oficial próprio.',
            'mainRisk': 'Diferenciar de clínicas com nome homônimo em outros estados.',
            'factualContent': 'Medium',
            'imageryLevel': 'Medium',
            'status': 'qualified'
        },
        {
            'slug': 'clinica-dra-francine-goulart-rio-claro',
            'placeId': 'ChIJ_francine_goulart_rc',
            'nome': 'Clínica Odontológica Dra. Francine Goulart',
            'nicho': 'Clínica Odontológica Geral',
            'cidade': 'Rio Claro, SP',
            'country': 'BR',
            'locale': 'pt-BR',
            'language': 'pt',
            'phoneCountryCode': '55',
            'nota': 4.8,
            'avaliacoes': 28,
            'telefone': '(19) 98849-4898',
            'whatsapp': '5519988494898',
            'email': None,
            'endCliente': 'Avenida 7, nº 310, Centro, Rio Claro - SP',
            'siteAntigo': None,
            'websiteStatus': 'none',
            'siteMode': 'new_site_concept',
            'opportunityType': 'NOVO SITE',
            'opportunityScore': 76,
            'classificationEvidence': 'Consultório ativo no Centro desde 2019 com telefone direto e sem website institucional.',
            'mainRisk': 'Menor detalhamento público prévio de lista de serviços.',
            'factualContent': 'Medium',
            'imageryLevel': 'Medium',
            'status': 'qualified'
        },
        {
            'slug': 'clinica-dr-carlos-laudares-rio-claro',
            'placeId': 'ChIJ_carlos_laudares_rc',
            'nome': 'Clínica Odontológica Dr. Carlos Laudares',
            'nicho': 'Implantes, Estética e Ortodontia',
            'cidade': 'Rio Claro, SP',
            'country': 'BR',
            'locale': 'pt-BR',
            'language': 'pt',
            'phoneCountryCode': '55',
            'nota': 4.9,
            'avaliacoes': 16,
            'telefone': '(19) 3524-7331',
            'whatsapp': '5519996584789',
            'email': None,
            'endCliente': 'Avenida 11, nº 633, Bairro Saúde, Rio Claro - SP',
            'siteAntigo': 'https://www.drcarloslaudares.com.br',
            'websiteStatus': 'healthy',
            'siteMode': 'redesign',
            'opportunityType': 'AUDIT_HEALTHY',
            'opportunityScore': 40,
            'classificationEvidence': 'Site verificado via navegador real: ativo, moderno, responsivo e mantido por agência (Aliança Produtora & MKT). Erro 403 anterior decorreu de bloqueio WAF em curl.',
            'mainRisk': 'Já possui agência ativa e presença funcional.',
            'factualContent': 'High',
            'imageryLevel': 'High',
            'status': 'discovered'
        }
    ]

    for lead in leads_import:
        res = discovery_service.upsert_lead_discovery(conn, lead, run_id=run_id)
        print(f"Upsert {lead['slug']}: {res}")

    print("\n=== TESTE 3: Verificação de Não-Duplicação em Repetição de Scan ===")
    count_antes = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    for lead in leads_import:
        discovery_service.upsert_lead_discovery(conn, lead, run_id=run_id)
    count_depois = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    print(f"Total leads antes: {count_antes}, depois de rescanning: {count_depois}")
    assert count_antes == count_depois, "Rescan não deve criar registros duplicados!"

    print("\n=== TESTE 4: Deduplicação por Fallback (Nome + Endereço sem Place ID) ===")
    lead_sem_place_id = {
        'nome': 'Instituto Ferreira Odontologia e Harmonização Orofacial',
        'endCliente': 'Rua 5, 3379, Jardim Portugal, Rio Claro - SP',
        'cidade': 'Rio Claro, SP',
        'nota': 5.0
    }
    dup_slug = discovery_service.encontrar_lead_duplicado(conn, lead_sem_place_id)
    print(f"Deduplicação por fallback identificou slug existente: {dup_slug}")
    assert dup_slug == 'instituto-ferreira-odontologia-rio-claro', "Fallback de deduplicação falhou!"

    print("\n=== TESTE 5: Proteção de Downstream Status ===")
    conn.execute("UPDATE leads SET status='redesenhado' WHERE slug='mb-odontologia-premium-rio-claro'")
    conn.commit()
    # Re-executa discovery upsert
    discovery_service.upsert_lead_discovery(conn, {
        'slug': 'mb-odontologia-premium-rio-claro',
        'nome': 'MB Odontologia Premium',
        'opportunityScore': 82
    })
    st_mb = conn.execute("SELECT status, opportunityScore FROM leads WHERE slug='mb-odontologia-premium-rio-claro'").fetchone()
    print(f"Status do lead após re-scan: {st_mb[0]} (Score atualizado: {st_mb[1]})")
    assert st_mb[0] == 'redesenhado', "Status downstream avançado não pode ser rebaixado para qualified/discovered!"

    print("\n=== TESTE 6: Verificação de Zero Envios de Mensagens / Outreach ===")
    out_count = conn.execute("SELECT COUNT(*) FROM outreach_history").fetchone()[0]
    print(f"Total de mensagens enviadas no histórico de outreach: {out_count}")
    assert out_count == 0, "Zero mensagens devem ter sido disparadas durante a fase de discovery!"

    conn.close()

    print("\n=== TESTE 7: Regeneração do dashboard.html ===")
    import subprocess
    res_mcp = subprocess.run(['python', os.path.join(PASTA, 'prospector-mcp.py'), '--pasta', PASTA],
                             input=b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"regenerar_dashboard","arguments":{}}}\n',
                             capture_output=True)
    # Regenera direto via python também para garantir
    from importlib import import_module
    mcp_mod = import_module('prospector-mcp')
    mcp_mod.f_dashboard()
    print("dashboard.html regenerado com sucesso!")

    # Restaura status qualified para consistência de discovery
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE leads SET status='qualified' WHERE slug='mb-odontologia-premium-rio-claro'")
    conn.commit(); conn.close()
    mcp_mod.f_dashboard()

    print("\nTODOS OS TESTES PASSARAM COM SUCESSO! [OK]")

if __name__ == '__main__':
    run_tests_and_import()
