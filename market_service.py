#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector — Serviço de Mercados, Países e Localização.
Gerencia resolução geográfica (BR, PT, etc.), normalização telefônica internacional
e adequação linguística (pt-BR vs pt-PT) sem suposições rígidas sobre o Brasil.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

MARKETS: Dict[str, Dict[str, Any]] = {
    "BR": {
        "country": "BR",
        "name": "Brasil",
        "locale": "pt-BR",
        "language": "pt",
        "phoneCountryCode": "55",
        "phoneNationalLengths": [10, 11],  # 2 DDD + 8 ou 9 dígitos
        "currency": "BRL",
        "currencySymbol": "R$",
        "keywords": ["brasil", "brazil", "br", "sp", "rj", "mg", "pr", "rs", "sc", "ba", "pe", "ce", "df", "go"],
        "cities": [
            "são paulo", "sao paulo", "campinas", "rio claro", "rio de janeiro", "curitiba",
            "porto alegre", "belo horizonte", "salvador", "brasília", "brasilia", "recife",
            "fortaleza", "santos", "sorocaba", "ribeirão preto", "ribeirao preto", "piracicaba"
        ],
        "ctas": {
            "whatsapp": "Conversar no WhatsApp",
            "book": "Agendar Consulta",
            "call": "Ligar Agora",
            "directions": "Como Chegar",
            "contact": "Fale Conosco",
        },
        "phrasing": {
            "demonstration_sub": "Já está no ar, em caráter de demonstração. Compare com a presença atual usando os botões abaixo — abra também no celular.",
            "cta_box": "Se gostou do que viu, me chama — te explico como funciona a publicação definitiva no seu domínio e tiro qualquer dúvida.",
            "mobile_term": "celular",
            "concept_organizes": "O que este conceito organiza",
            "concept_repensado": "O que foi repensado",
            "new_site_wpp": "Como notei que vocês ainda não possuem um site próprio oficial para facilitar o contato e agendamento de clientes, tomei a liberdade de preparar um conceito exclusivo para demonstração:",
            "new_site_email_subj": "{nome}, uma ideia de site próprio para o seu negócio",
            "new_site_email_p": "Notei que o negócio ainda não conta com uma página web oficial própria para centralizar informações, localização e agendamentos diretos.",
        }
    },
    "PT": {
        "country": "PT",
        "name": "Portugal",
        "locale": "pt-PT",
        "language": "pt",
        "phoneCountryCode": "351",
        "phoneNationalLengths": [9],  # 9 dígitos (91, 92, 93, 96, 21, 22, etc.)
        "currency": "EUR",
        "currencySymbol": "€",
        "keywords": ["portugal", "pt", "lisboa", "porto", "braga", "coimbra", "faro", "aveiro", "setubal", "setúbal", "leiria", "funchal", "viseu", "guimarães", "guimaraes", "cascais", "sintra", "oeiras", "algarve"],
        "cities": [
            "lisboa", "porto", "braga", "coimbra", "faro", "aveiro", "setúbal", "setubal",
            "leiria", "funchal", "viseu", "guimarães", "guimaraes", "cascais", "sintra",
            "oeiras", "matosinhos", "almada", "évora", "evora", "portimão", "portimao"
        ],
        "ctas": {
            "whatsapp": "Contactar no WhatsApp",
            "book": "Marcar Consulta",
            "call": "Ligar",
            "directions": "Como Chegar",
            "contact": "Contactar",
        },
        "phrasing": {
            "demonstration_sub": "Já se encontra online, em caráter demonstrativo. Compare com a presença atual utilizando os botões abaixo — abra também no telemóvel.",
            "cta_box": "Se gostou da proposta, envie-me uma mensagem — explico prontamente como funciona a publicação definitiva no vosso domínio e esclareço qualquer dúvida.",
            "mobile_term": "telemóvel",
            "concept_organizes": "O que este conceito organiza",
            "concept_repensado": "O que foi repensado",
            "new_site_wpp": "Como reparei que ainda não dispõem de um site oficial próprio para centralizar contactos e marcações diretas, tomei a liberdade de preparar uma proposta de site exclusiva para demonstração:",
            "new_site_email_subj": "{nome}, uma proposta de site próprio para o vosso espaço",
            "new_site_email_p": "Reparei que o negócio ainda não conta com uma página web oficial própria para centralizar informações, localização e marcações diretas.",
        }
    }
}


def resolve_market(country_code: Optional[str] = None, default: str = "BR") -> Dict[str, Any]:
    """Obtém metadados do mercado pelo código ISO do país (BR, PT)."""
    code = (country_code or "").strip().upper()
    if code in MARKETS:
        return MARKETS[code]
    return MARKETS.get(default.upper(), MARKETS["BR"])


def detect_country(
    query_or_city: Optional[str] = None,
    address: Optional[str] = None,
    default_country: str = "BR"
) -> Tuple[str, str, str, str]:
    """
    Detecta o país, locale, idioma e código telefônico a partir de pistas de busca ou endereço.
    Retorna (country, locale, language, phoneCountryCode).
    Caso inconclusivo, retorna ('unknown', 'pt-BR', 'pt', None) ou fallback seguro.
    """
    text = f"{query_or_city or ''} {address or ''}".lower()
    
    # 1. Checagem explícita para Portugal
    for kw in MARKETS["PT"]["keywords"]:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            pt = MARKETS["PT"]
            return pt["country"], pt["locale"], pt["language"], pt["phoneCountryCode"]
    for c in MARKETS["PT"]["cities"]:
        if c in text:
            pt = MARKETS["PT"]
            return pt["country"], pt["locale"], pt["language"], pt["phoneCountryCode"]

    # 2. Checagem explícita para Brasil
    for kw in MARKETS["BR"]["keywords"]:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            br = MARKETS["BR"]
            return br["country"], br["locale"], br["language"], br["phoneCountryCode"]
    for c in MARKETS["BR"]["cities"]:
        if c in text:
            br = MARKETS["BR"]
            return br["country"], br["locale"], br["language"], br["phoneCountryCode"]

    # 3. Fallback do config se especificado e válido
    def_code = (default_country or "").strip().upper()
    if def_code in MARKETS:
        m = MARKETS[def_code]
        return m["country"], m["locale"], m["language"], m["phoneCountryCode"]

    return "unknown", "pt-BR", "pt", ""


def normalize_phone_by_country(raw: str, country: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Normaliza telefone para formato canônico internacional (dígitos E.164 sem '+').
    Se o país for conhecido (BR, PT), aceita números locais e adiciona DDI.
    Se o país for desconhecido, só aceita números com DDI explícito ou formato internacional.
    """
    if not raw or not isinstance(raw, str):
        return None, "Número não informado."

    clean = re.sub(r"\D", "", raw)
    has_plus = raw.strip().startswith("+")
    c_code = (country or "").strip().upper()

    if not clean:
        return None, "Número inválido (sem dígitos)."

    # 1. Tratamento quando país é PORTUGAL (PT)
    if c_code == "PT":
        if clean.startswith("351"):
            if len(clean) == 12:  # 351 + 9 dígitos
                return clean, None
            return None, "Número de Portugal com DDI deve conter 351 + 9 dígitos (ex: 351912345678)."
        if len(clean) == 9:  # Número local português
            return "351" + clean, None
        if has_plus and 10 <= len(clean) <= 15:
            return clean, None
        return None, "Número de Portugal inválido. Esperado: 9 dígitos nacionais ou DDI 351 + 9 dígitos."

    # 2. Tratamento quando país é BRASIL (BR)
    if c_code == "BR":
        if clean.startswith("55"):
            if len(clean) in (12, 13):
                return clean, None
            return None, "Número brasileiro com DDI deve conter 55 + DDD (2 dígitos) + 8 ou 9 dígitos."
        if len(clean) in (10, 11):  # Número local brasileiro (DDD + número)
            return "55" + clean, None
        if has_plus and 10 <= len(clean) <= 15:
            return clean, None
        return None, "Número brasileiro inválido. Esperado: DDD (2 dígitos) + 8/9 dígitos (ex: 11999999999)."

    # 3. Tratamento quando país é DESCONHECIDO (unknown)
    # Se possui '+' explícito no início, aceitamos como internacional direto
    if has_plus:
        if 10 <= len(clean) <= 15:
            return clean, None
        return None, "Número internacional com '+' deve conter entre 10 e 15 dígitos."

    # Se começa com 55 ou 351 com tamanho exato
    if clean.startswith("55") and len(clean) in (12, 13):
        return clean, None
    if clean.startswith("351") and len(clean) == 12:
        return clean, None

    return None, "País do lead não identificado com segurança. Informe o telefone no formato internacional com código de país (ex: +351... ou +55...)."
