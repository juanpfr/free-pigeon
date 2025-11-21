import requests

def buscar_cep(cep):
    cep = cep.replace("-", "").strip()

    # CEP deve ter 8 dígitos
    if not cep.isdigit() or len(cep) != 8:
        return None

    url = f"https://viacep.com.br/ws/{cep}/json/"

    try:
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()  # levanta exceção em códigos 4xx ou 5xx
        dados = resposta.json()
    except Exception:
        return None  # evita traceback

    if dados.get("erro"):
        return None

    return {
        "cep": dados.get("cep"),
        "logradouro": dados.get("logradouro"),
        "bairro": dados.get("bairro"),
        "cidade": dados.get("localidade"),
        "uf": dados.get("uf"),
    }
