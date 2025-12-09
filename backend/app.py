
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, random, uuid, time, threading

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)

CACHE_TTL = int(os.getenv('CACHE_TTL_SECONDS', '300'))

_cache = {}
_cache_lock = threading.Lock()

def _set_cache(key, payload, ttl=CACHE_TTL):
    expiry = time.time() + int(ttl)
    with _cache_lock:
        _cache[key] = (payload, expiry)

def _get_cache(key):
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        payload, expiry = entry
        if time.time() > expiry:
            del _cache[key]
            return None
        return payload

with open('brands.json','r') as f:
    BRANDS = json.load(f)

def compute_recommendation(answers):
    score = 0
    if answers.get('strap') == 'falling':
        score += 2
    if answers.get('shape') == 'shallow':
        score += 1
    if answers.get('settle') == 'spread':
        score += 1
    if score >= 3:
        return 'Full Coverage'
    elif score == 2:
        return 'Balconette'
    elif score == 1:
        return 'T-Shirt Bra'
    else:
        return 'Regular Bra'

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json or {}
    data.pop('mobile', None); data.pop('phone', None)
    answers = data.get('answers', {})
    recommended = compute_recommendation(answers)
    samples = []
    for b in BRANDS:
        matching = [s for s in b['styles'] if recommended.lower().split()[0] in s['name'].lower()]
        chosen = random.choice(matching if matching else b['styles'])
        samples.append({'brand': b['brand'], 'style': chosen})
    session_id = str(uuid.uuid4())
    payload = {'recommended_category': recommended, 'samples': samples}
    _set_cache(f'fit:{session_id}', json.dumps(payload), CACHE_TTL)
    return jsonify({'session_id': session_id, 'result': payload, 'ttl_seconds': CACHE_TTL})

@app.route('/api/result/<session_id>', methods=['GET'])
def get_result(session_id):
    raw = _get_cache(f'fit:{session_id}')
    if not raw:
        return jsonify({'error': 'session not found or expired'}), 404
    return jsonify(json.loads(raw))

@app.route('/')
def index_root():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(e):
    try:
        return app.send_static_file('index.html')
    except Exception:
        return jsonify({'error': 'not found'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
