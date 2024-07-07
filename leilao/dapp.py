import os
import logging
import requests
import json
import random
from hexbytes import HexBytes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 
rollup_server = os.getenv("ROLLUP_HTTP_SERVER_URL")

beneficiary = "beneficiary"  
minimum_bid_value = random.randint(50, 150)

current_bid = 0
current_bid_user = ""

user_balances = {beneficiary: 0}

# Funções auxiliares
def hex2str(h):
    return bytes.fromhex(h[2:]).decode("utf-8")

def str2hex(s):
    return "0x" + s.encode("utf-8").hex()

def post(endpoint, json_data):
    try:
        response = requests.post(f"{rollup_server}/{endpoint}", json=json_data)
        logger.info(f"Received {endpoint} status {response.status_code} body {response.content}")
        return response
    except Exception as e:
        logger.error(f"Error posting to {endpoint}: {e}")
        return None

# Handlers
def handle_create_account(payload_json):
    global user_balances

    username = payload_json["params"]["name"]
    balance = int(payload_json["params"]["balance"])

    if username in user_balances:
        logger.warning(f"Account already exists for user: {username}")
        return "reject"
    
    user_balances[username] = balance
    logger.info(f"Account created for user: {username} with balance: {balance}")
    return "accept"

def handle_send_bid(payload_json):
    global current_bid, current_bid_user, user_balances

    bid_value = int(payload_json["params"]["value"])
    username = payload_json["params"]["name"]
    logger.info(f"Bid value received: {bid_value} from user: {username}")

    if username not in user_balances:
        logger.warning(f"User {username} does not have an account")
        return "reject"

    if bid_value > minimum_bid_value and bid_value > current_bid and user_balances[username] >= bid_value:
        if current_bid_user:
            user_balances[current_bid_user] += current_bid
        
        user_balances[username] -= bid_value
        current_bid = bid_value
        current_bid_user = username
        logger.info(f"Valid bid received: {bid_value} from user: {username}")
        return "accept"
    else:
        logger.warning(f"Invalid bid received: {bid_value} from user: {username}")
        return "reject"

def handle_end_auction(payload_json):
    global current_bid, current_bid_user, user_balances, minimum_bid_value

    if current_bid_user:
        user_balances[beneficiary] += current_bid
        logger.info(f"Auction ended. Highest bid: {current_bid} from user: {current_bid_user}")
        logger.info(f"Beneficiary {beneficiary} new balance: {user_balances[beneficiary]}")
        
        # Reset para o próximo leilão
        current_bid = 0
        current_bid_user = ""
        minimum_bid_value = random.randint(50, 150)
        logger.info(f"Next auction minimum bid value: {minimum_bid_value}")
        
        return "accept"
    else:
        logger.warning("No bids were placed during the auction.")
        return "reject"

def handle_inspect(payload_json):
    state = {
        "beneficiary": beneficiary,
        "minimumBidValue": minimum_bid_value,
        "currentBid": current_bid,
        "currentBidUser": current_bid_user,
        "userBalances": user_balances
    }
    logger.info(f"Sending state for inspection: {state}")
    post("report", {"payload": str2hex(json.dumps(state))})
    return "accept"

def handle_advance(data):
    try:
        payload_hex = data.get("payload")
        payload_json = json.loads(hex2str(payload_hex))
    except Exception as e:
        logger.error(f"Error decoding payload hex: {e}")
        return "reject"

    action = payload_json.get("action")
    logger.info(f"Received advance state request with action: {action}")

    if action == "createAccount":
        return handle_create_account(payload_json)
    elif action == "sendBid":
        return handle_send_bid(payload_json)
    elif action == "endAuction":
        return handle_end_auction(payload_json)
    else:
        logger.warning(f"Unknown action received: {action}")
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
            logger.info("No pending requests, trying again...")
            continue 

        if response.status_code != 200:
            logger.error(f"Error in request to Rollup server: {response.status_code} - {response.text}")
            continue
        
        try:
            rollup_request = response.json()
            data = rollup_request["data"]
            handler = handlers.get(rollup_request["request_type"], lambda _: "reject")
            logger.info(f"Processing request of type: {rollup_request['request_type']}")
            
            finish["status"] = handler(data)
            logger.info(f"Processing result: {finish['status']}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {e} - {response.text}")
            continue
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        break
