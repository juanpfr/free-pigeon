import requests

def buscar_cep(cep):
    cep = cep.replace("-", "").strip()
    url = f"https://viacep.com.br/ws/{cep}/json/"
    resposta = requests.get(url)

    if resposta.status_code == 200:
        dados = resposta.json()
        if "erro" not in dados:
            return {
                "cep": dados.get("cep"),
                "logradouro": dados.get("logradouro"),
                "bairro": dados.get("bairro"),
                "cidade": dados.get("localidade"),
                "uf": dados.get("uf"),
            }
    return None

