from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# ---------- النظام الأول: رصيد الموبايل ----------
def balance_login(username, password):
    url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    headers = {
        'User-Agent': 'okhttp/4.11.0',
        'Accept': 'application/json',
        'silentLogin': 'false',
        'x-agent-operatingsystem': '15',
        'clientId': 'AnaVodafoneAndroid',
        'Accept-Language': 'ar',
        'x-agent-device': 'Samsung SM-A165F',
        'x-agent-version': '2024.11.2',
        'x-agent-build': '1200',
        'digitalId': '25VT5Q5QUDYYV'
    }
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_secret': '95fd95fb-7489-4958-8ae6-d31a525cd20a',
        'client_id': 'ana-vodafone-app'
    }
    try:
        r = requests.post(url, data=data, headers=headers, timeout=30)
        if r.status_code == 200:
            token = r.json().get('access_token')
            return True, token, "تم تسجيل الدخول"
        else:
            return False, None, "فشل الدخول"
    except Exception as e:
        return False, None, str(e)

def balance_purchase(token, msisdn, card_id):
    url = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
    payload = {
        "channel": {"name": "MobileApp"},
        "orderItem": [{
            "action": "insert",
            "product": {
                "id": card_id,
                "relatedParty": [{"id": msisdn, "name": "MSISDN", "role": "Subscriber"}]
            },
            "eCode": 0
        }],
        "@type": "FakkaAndMared"
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'msisdn': msisdn,
        'Content-Type': 'application/json',
        'api-host': 'ProductOrderingManagement',
        'useCase': 'FakkaAndMaredProduct',
        'api-version': 'v2',
        'User-Agent': 'okhttp/4.11.0',
        'Accept': 'application/json'
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code in (200, 201) and r.json().get('state') == 'Completed':
            return True, "تم الشراء"
        return False, "فشل الشراء"
    except Exception as e:
        return False, str(e)

# ---------- النظام الثاني: كاش ----------
def get_seamless_and_msisdn():
    url = "http://mobile.vodafone.com.eg/checkSeamless/realms/vf-realm/protocol/openid-connect/auth"
    params = {'client_id': 'cash-app'}
    headers = {
        'User-Agent': 'okhttp/4.12.0',
        'x-agent-operatingsystem': '16',
        'clientId': 'AnaVodafoneAndroid',
        'Accept-Language': 'ar',
        'x-agent-device': 'Samsung SM-M52',
        'x-agent-version': '2025.11.1',
        'digitalId': '',
        'device-id': 'b26ba335813fad21'
    }
    r = requests.get(url, params=params, headers=headers, timeout=30)
    if r.status_code != 200:
        raise Exception("فشل seamlessToken")
    data = r.json()
    raw = data['msisdn']
    formatted = '0' + raw if raw.startswith('1') else raw
    return data['seamlessToken'], formatted

def get_cash_token(seamless_token):
    url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    data = {
        'grant_type': 'password',
        'client_secret': 'b86e30a8-ae29-467a-a71f-65c73f2ff5e3',
        'client_id': 'cash-app'
    }
    headers = {
        'User-Agent': 'okhttp/4.12.0',
        'silentLogin': 'true',
        'seamlessToken': seamless_token,
        'firstTimeLogin': 'true',
        'x-agent-operatingsystem': '16',
        'clientId': 'AnaVodafoneAndroid',
        'Accept-Language': 'ar'
    }
    r = requests.post(url, data=data, headers=headers, timeout=30)
    if r.status_code != 200:
        raise Exception("فشل access_token")
    return r.json()['access_token']

def cash_purchase(cash_token, sender, receiver, pin, card_id):
    url = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
    payload = {
        "channel": {"name": "MobileApp"},
        "orderItem": [{
            "action": "insert",
            "id": card_id,
            "product": {
                "characteristic": [
                    {"name": "PaymentMethod", "value": "VFCash"},
                    {"name": "USE_EMONEY", "value": "False"},
                    {"name": "MerchantCode", "value": "81841829"}
                ],
                "id": card_id,
                "relatedParty": [
                    {"id": sender, "name": "MSISDN", "role": "Subscriber"},
                    {"id": "Receiver", "name": "Receiver", "role": receiver}
                ]
            },
            "@type": "Fakka_2.5_Unite",
            "eCode": 0
        }],
        "relatedParty": [{"id": pin, "name": "pin", "role": "Requestor"}],
        "@type": "CashFakkaAndMared"
    }
    headers = {
        'Authorization': f'Bearer {cash_token}',
        'msisdn': sender,
        'Content-Type': 'application/json',
        'useCase': 'CashFakkaAndMared',
        'api-version': 'v2',
        'User-Agent': 'okhttp/4.12.0',
        'Accept': 'application/json'
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    if r.status_code == 200 and r.json().get('code') == '0000':
        return True, "تم الشراء من كاش"
    return False, "فشل الشراء من كاش"

# ---------- روتات API ----------
@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Vodafone API (Balance + Cash)"})

# رصيد الموبايل
@app.route('/api/balance/login', methods=['POST'])
def api_balance_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ok, token, msg = balance_login(username, password)
    if ok:
        return jsonify({"success": True, "message": msg, "token": token, "msisdn": username})
    return jsonify({"success": False, "message": msg})

@app.route('/api/balance/purchase', methods=['POST'])
def api_balance_purchase():
    data = request.json
    token = data.get('token')
    msisdn = data.get('msisdn')
    card_id = data.get('card_id')
    ok, msg = balance_purchase(token, msisdn, card_id)
    return jsonify({"success": ok, "message": msg})

# كاش
@app.route('/api/cash/login', methods=['POST'])
def api_cash_login():
    try:
        seamless, msisdn = get_seamless_and_msisdn()
        cash_token = get_cash_token(seamless)
        return jsonify({"success": True, "message": "تم تسجيل الدخول", "token": cash_token, "msisdn": msisdn})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/cash/purchase', methods=['POST'])
def api_cash_purchase():
    data = request.json
    token = data.get('token')
    sender = data.get('msisdn')
    receiver = data.get('receiver')
    pin = data.get('pin')
    card_id = data.get('card_id')
    ok, msg = cash_purchase(token, sender, receiver, pin, card_id)
    return jsonify({"success": ok, "message": msg})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
