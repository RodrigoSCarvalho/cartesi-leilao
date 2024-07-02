import os
import logging
import requests
import json
from hexbytes import HexBytes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
rollup_server = os.getenv("ROLLUP_HTTP_SERVER_URL")

# Endereço do beneficiário e configurações do leilão
beneficiario = "0x..."  # Endereço do beneficiário
valor_minimo_lance = 100
tempo_total_leilao = 3600

# Variáveis de estado do leilão
lance_atual = 0
usuario_lance_atual = ""

# Handlers simplificados
def handle_advance(data):
    global lance_atual, usuario_lance_atual

    logger.info(f"Received advance state request with data: {data}")
    
    try:
        payload_hex = data.get("payload")
        # Remove os dois primeiros caracteres "0x"
        payload_hex_clean = payload_hex[2:]
        payload_json = json.loads(HexBytes(payload_hex_clean).decode())
    except Exception as e:
        logger.error(f"Erro ao decodificar o payload hex: {e}")
        return "reject"
    
    action = payload_json.get("action")
    logger.info(f"Received advance state request with action: {action}")
    
    if action == "enviarLance":
        valor_lance = int(payload_json["params"]["value"])
        nome_usuario = payload_json["params"]["name"]
        logger.info(f"Valor do lance recebido: {valor_lance} do usuário: {nome_usuario}")
        
        # Verificar se o lance é válido
        if valor_lance > valor_minimo_lance and valor_lance > lance_atual:
            lance_atual = valor_lance
            usuario_lance_atual = nome_usuario
            logger.info(f"Lance válido recebido: {valor_lance} do usuário: {nome_usuario}")
            return "accept"
        else:
            logger.warning(f"Lance inválido recebido: {valor_lance}")
            return "reject"
    elif action == "encerrarLeilao":
        logger.info("Recebido pedido para encerrar o leilão.")
        
        # Lógica para encerrar o leilão e transferir fundos
        logger.info("Encerrando o leilão e transferindo fundos...")
        logger.info(f"Leilão encerrado. Maior lance: {lance_atual} do usuário: {usuario_lance_atual}")
        
        return "accept"
    else:
        logger.warning(f"Ação desconhecida recebida: {action}")
        return "reject"

def handle_inspect(data):
    logger.info(f"Received inspect state request with data: {data}")
    
    try:
        payload_hex = data.get("payload")
        # Remove os dois primeiros caracteres "0x"
        payload_hex_clean = payload_hex[2:]
        logger.info(f"Received inspect state request with payload_hex_clean: {payload_hex_clean}")
        payload_json = json.loads(HexBytes(payload_hex_clean).decode())
        logger.info(f"Received inspect state request with payload_json: {payload_json}")
    except Exception as e:
        logger.error(f"Erro ao decodificar o payload hex: {e}")
        return "reject"
    
    action = payload_json.get("action")
    logger.info(f"Received inspect state request with action: {action}")
    
    if action == "verificarEstado":
        estado = {
            "beneficiario": beneficiario,
            "valorMinimoLance": valor_minimo_lance,
            "tempoTotalLeilao": tempo_total_leilao,
            "lanceAtual": lance_atual,
            "usuarioLanceAtual": usuario_lance_atual
        }
        logger.info(f"Enviando estado para inspeção: {estado}")
        response = requests.post(rollup_server + "/report", json={"payload": "0x"+json.dumps(estado).encode("utf-8").hex()})
        return "accept"
            
    else:
        logger.warning(f"Ação desconhecida recebida: {action}")
        return "reject"

# Loop principal
handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}

while True:
    try:
        response = requests.post(rollup_server + "/finish", json=finish)
        if response.status_code == 202:
            logger.info("Nenhuma solicitação pendente, tentando novamente...")
            continue  # Sem solicitação pendente, tentando novamente

        if response.status_code != 200:
            logger.error(f"Erro na solicitação ao servidor Rollup: {response.status_code} - {response.text}")
            continue
        
        try:
            rollup_request = response.json()
            data = rollup_request["data"]
            handler = handlers.get(rollup_request["request_type"], lambda _: "reject")
            logger.info(f"Processando solicitação de tipo: {rollup_request['request_type']}")
            
            finish["status"] = handler(data)
            logger.info(f"Resultado do processamento: {finish['status']}")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar a resposta JSON: {e} - {response.text}")
            continue
    except Exception as e:
        logger.error(f"Erro no loop principal: {e}")
        break
