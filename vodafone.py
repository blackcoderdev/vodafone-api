import requests
import json
import time

class VodafoneEgypt:
    def __init__(self):
        self.base_url = "https://mobile.vodafone.com.eg"
        self.token = None
        self.msisdn = None
        self.session = requests.Session()
        
    def login(self, username, password):
        url = f"{self.base_url}/auth/realms/vf-realm/protocol/openid-connect/token"
        
        payload = {
            'grant_type': "password",
            'username': username,
            'password': password,
            'client_secret': "95fd95fb-7489-4958-8ae6-d31a525cd20a",
            'client_id': "ana-vodafone-app"
        }
        
        headers = {
            'User-Agent': "okhttp/4.11.0",
            'Accept': "application/json",
            'silentLogin': "false",
            'x-agent-operatingsystem': "15",
            'clientId': "AnaVodafoneAndroid",
            'Accept-Language': "ar",
            'x-agent-device': "Samsung SM-A165F",
            'x-agent-version': "2024.11.2",
            'x-agent-build': "1200",
            'digitalId': "25VT5Q5QUDYYV"
        }
        
        try:
            response = self.session.post(url, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'access_token' in data:
                self.token = data['access_token']
                self.msisdn = username
                return True, "تم تسجيل الدخول بنجاح"
            else:
                return False, "فشل تسجيل الدخول"
        except Exception as e:
            return False, str(e)
    
    def get_available_cards(self):
        return [
            "Fakka_7_Unite", "Fakka_7_Social", "Fakka_2.5_Unite", 
            "Fakka_2.5_Social", "Fakka_4.25_Unite", "Fakka_4.25_Social",
            "Fakka_9_Unite", "Fakka_9_Social", "Fakka_10.5_Unite",
            "Fakka_11.5_Unite", "Fakka_12_Unite", "Fakka_13_Unite",
            "Fakka_15.5_Unite", "Fakka_16.5_Unite", "Fakka_17.5_Unite",
            "Fakka_19.5_NewUnite", "Fakka_26_Unite", "Mared_10_Minuts",
            "Mared_10_Flexs", "Mared_10_Social"
        ]
    
    def extract_price(self, card_id):
        parts = card_id.split('_')
        for part in parts:
            if part.replace('.', '').isdigit():
                return part
        return "غير معروف"
    
    def purchase_card(self, card_id):
        if not self.token:
            return False, "الرجاء تسجيل الدخول أولاً"
        
        url = f"{self.base_url}/services/dxl/pom/productOrder"
        
        payload = {
            "channel": {"name": "MobileApp"},
            "orderItem": [{
                "action": "insert",
                "product": {
                    "id": card_id,
                    "relatedParty": [{"id": self.msisdn, "name": "MSISDN", "role": "Subscriber"}]
                },
                "eCode": 0
            }],
            "@type": "FakkaAndMared"
        }
        
        headers = {
            'Content-Type': "application/json",
            'api-host': "ProductOrderingManagement",
            'useCase': "FakkaAndMaredProduct",
            'Authorization': f"Bearer {self.token}",
            'api-version': "v2",
            'x-agent-operatingsystem': "15",
            'clientId': "AnaVodafoneAndroid",
            'x-agent-device': "Samsung SM-A165F",
            'x-agent-version': "2024.11.2",
            'x-agent-build': "1200",
            'msisdn': self.msisdn,
            'Accept-Language': "ar"
        }
        
        try:
            time.sleep(1)
            response = self.session.post(url, data=json.dumps(payload), headers=headers)
            
            if response.status_code == 400:
                return False, "رصيد غير كافي"
            elif response.status_code == 429:
                return False, "تم حظر الطلبات مؤقتاً"
            elif response.status_code in [200, 201]:
                result = response.json()
                if result.get('state') == 'Completed':
                    return True, f"تم شراء {card_id} بنجاح"
                else:
                    return False, "فشلت العملية"
            elif response.status_code == 401:
                return False, "انتهت الجلسة، سجل دخول مرة أخرى"
            else:
                return False, f"خطأ {response.status_code}"
        except Exception as e:
            return False, str(e)
