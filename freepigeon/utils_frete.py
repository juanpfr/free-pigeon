# freepigeon/utils_frete.py
import requests
from decimal import Decimal
import xml.etree.ElementTree as ET


def calcular_frete_correios(
    cep_origem: str,
    cep_destino: str,
    peso_kg: Decimal,
    comprimento: int = 20,
    altura: int = 5,
    largura: int = 15,
    diametro: int = 0,
):
    """
    Usa o webservice oficial dos Correios (CalcPrecoPrazo) sem contrato.
    Retorna lista de opções de frete (PAC / SEDEX).

    Se der qualquer problema na requisição ou parse, retorna [].
    """

    # IMPORTANTE: usar HTTPS
    url = "https://ws.correios.com.br/calculador/CalcPrecoPrazo.asmx/CalcPrecoPrazo"

    # Correios querem peso em kg, com ponto decimal
    peso_str = str(peso_kg).replace(",", ".")

    # Códigos sem contrato: 04510 = PAC, 04014 = SEDEX
    servicos = {
        "04510": "PAC",
        "04014": "SEDEX",
    }

    resultados = []

    for codigo_servico, nome_servico in servicos.items():
        params = {
            "nCdEmpresa": "",
            "sDsSenha": "",
            "nCdServico": codigo_servico,
            "sCepOrigem": cep_origem,
            "sCepDestino": cep_destino,
            "nVlPeso": peso_str,
            "nCdFormato": 1,                # caixa/pacote
            "nVlComprimento": comprimento,
            "nVlAltura": altura,
            "nVlLargura": largura,
            "nVlDiametro": diametro,
            "sCdMaoPropria": "N",
            "nVlValorDeclarado": "0",
            "sCdAvisoRecebimento": "N",
            "StrRetorno": "xml",
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
        except requests.RequestException as e:
            # problema de rede/DNS/SSL
            print(f"[CORREIOS] Erro de requisição para {nome_servico}: {e}")
            continue

        if resp.status_code != 200:
            print(f"[CORREIOS] Status HTTP {resp.status_code} para {nome_servico}")
            continue

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            print(f"[CORREIOS] Erro ao parsear XML ({nome_servico}): {e}")
            continue

        servico = root.find(".//cServico")
        if servico is None:
            print(f"[CORREIOS] XML sem cServico para {nome_servico}")
            continue

        erro = (servico.findtext("Erro") or "").strip()
        if erro != "0":
            msg_erro = servico.findtext("MsgErro") or ""
            print(f"[CORREIOS] Erro {erro} em {nome_servico}: {msg_erro}")
            continue

        valor_str = (servico.findtext("Valor") or "0")
        prazo_str = (servico.findtext("PrazoEntrega") or "0")

        # Corrige formato R$ "25,90" -> "25.90"
        valor_str = valor_str.replace(".", "").replace(",", ".")
        try:
            valor = float(valor_str)
            prazo = int(prazo_str)
        except ValueError:
            print(f"[CORREIOS] Erro ao converter valor/prazo para {nome_servico}: {valor_str} / {prazo_str}")
            continue

        resultados.append({
            "codigo": nome_servico,
            "nome": f"{nome_servico} - Correios",
            "valor": valor,
            "prazo_dias": prazo,
        })

    return resultados
