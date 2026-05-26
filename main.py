from flask import Flask, request, jsonify
from flask_cors import CORS
from vodafone import VodafoneEgypt

app = Flask(__name__)
CORS(app)

# تخزين الجلسات النشطة مؤقتاً
sessions = {}

@app.route('/api', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'message': 'Vodafone API is running on Railway',
        'endpoints': {
            'POST /api/login': 'تسجيل الدخول',
            'GET /api/cards': 'جلب الكروت المتاحة',
            'POST /api/purchase': 'شراء كارت'
        }
    })

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'الرجاء إدخال الرقم وكلمة المرور'})
        
        vf = VodafoneEgypt()
        success, message = vf.login(username, password)
        
        if success:
            sessions[username] = vf
            return jsonify({
                'success': True,
                'message': message,
                'token': vf.token,
                'msisdn': username
            })
        else:
            return jsonify({'success': False, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/cards', methods=['GET'])
def get_cards():
    try:
        # البحث عن جلسة نشطة
        for session_id, vf in sessions.items():
            if vf.token:
                cards = vf.get_available_cards()
                cards_list = []
                for card in cards:
                    cards_list.append({
                        'id': card,
                        'name': card.replace('_', ' '),
                        'price': vf.extract_price(card),
                        'type': 'فكة' if 'Fakka' in card else 'مارد'
                    })
                return jsonify({'success': True, 'cards': cards_list})
        return jsonify({'success': False, 'message': 'لا توجد جلسة نشطة، سجل دخول أولاً'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/purchase', methods=['POST'])
def purchase():
    try:
        data = request.json
        card_id = data.get('card_id')
        msisdn = data.get('msisdn')
        
        if not card_id:
            return jsonify({'success': False, 'message': 'الرجاء تحديد الكارت'})
        
        if msisdn and msisdn in sessions:
            vf = sessions[msisdn]
        else:
            # البحث عن أي جلسة نشطة
            for session_id, vf in sessions.items():
                if vf.token:
                    break
            else:
                return jsonify({'success': False, 'message': 'سجل دخول أولاً'})
        
        success, message = vf.purchase_card(card_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
