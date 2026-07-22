from flask import Flask, redirect, request, jsonify, session
from flask_cors import CORS
from urllib.parse import quote
import requests
import os
import json

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-me')

# ============================================================
# CONFIGURATION
# ============================================================
TRELLO_API_KEY = os.environ.get('TRELLO_API_KEY', '')
TRELLO_API_SECRET = os.environ.get('TRELLO_API_SECRET', '')
TRELLO_REDIRECT_URI = os.environ.get('TRELLO_REDIRECT_URI', 'https://trello-genius-backend.onrender.com/auth/callback')
AUTH_SUCCESS_URL = os.environ.get('AUTH_SUCCESS_URL', 'https://hassaan-ahmed825.github.io/trello-insights/?auth=success')

# ============================================================
# ROUTES
# ============================================================
@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'service': 'Trello Genius Backend',
        'endpoints': [
            '/auth/trello',
            '/auth/callback',
            '/api/boards',
            '/api/lists/<board_id>',
            '/api/cards/<board_id>',
            '/api/health'
        ]
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/auth/trello')
def auth_trello():
    """Step 1: Redirect user to Trello for authorization."""
    if not TRELLO_API_KEY:
        return jsonify({'error': 'TRELLO_API_KEY not configured'}), 500
    
    # URL-encode the return_url
    encoded_return_url = quote(TRELLO_REDIRECT_URI, safe='')
    
    url = (
        f'https://trello.com/1/authorize'
        f'?return_url={encoded_return_url}'
        f'&callback_method=fragment'
        f'&expiration=never'
        f'&name=Trello%20Genius'
        f'&scope=read,write'
        f'&response_type=token'
        f'&key={TRELLO_API_KEY}'
    )
    return redirect(url)

@app.route('/auth/callback')
def auth_callback():
    """Step 2: Trello redirects back here with token."""
    token = request.args.get('token')
    
    if token:
        session['trello_token'] = token
        session['trello_api_key'] = TRELLO_API_KEY
        return redirect(f'{AUTH_SUCCESS_URL}&token={token[:10]}...')
    
    return '''
    <html>
        <body style="background:#0A0E1A;color:#E8EDF5;font-family:Arial;text-align:center;padding:50px;">
            <h1 style="color:#FF5252;">❌ Authorization Failed</h1>
            <p>Could not get token from Trello. Please try again.</p>
            <a href="/auth/trello" style="color:#00D4FF;">Try Again</a>
        </body>
    </html>
    ''', 400

@app.route('/api/boards')
def get_boards():
    token = session.get('trello_token')
    api_key = session.get('trello_api_key', TRELLO_API_KEY)
    
    if not token:
        return jsonify({'error': 'Not authenticated. Please connect Trello first.'}), 401
    
    try:
        response = requests.get(
            'https://api.trello.com/1/members/me/boards',
            params={
                'key': api_key,
                'token': token,
                'fields': 'id,name,url,desc,dateLastActivity'
            }
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch boards: {str(e)}'}), 500

@app.route('/api/lists/<board_id>')
def get_lists(board_id):
    token = session.get('trello_token')
    api_key = session.get('trello_api_key', TRELLO_API_KEY)
    
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        response = requests.get(
            f'https://api.trello.com/1/boards/{board_id}/lists',
            params={
                'key': api_key,
                'token': token,
                'fields': 'id,name,closed'
            }
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cards/<board_id>')
def get_cards(board_id):
    token = session.get('trello_token')
    api_key = session.get('trello_api_key', TRELLO_API_KEY)
    
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        response = requests.get(
            f'https://api.trello.com/1/boards/{board_id}/cards',
            params={
                'key': api_key,
                'token': token,
                'fields': 'id,name,due,dueComplete,idList,dateLastActivity,closed,desc,labels,idMembers',
                'members': 'true',
                'member_fields': 'fullName',
                'badges': 'true'
            }
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/board/<board_id>')
def get_board(board_id):
    token = session.get('trello_token')
    api_key = session.get('trello_api_key', TRELLO_API_KEY)
    
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        response = requests.get(
            f'https://api.trello.com/1/boards/{board_id}',
            params={
                'key': api_key,
                'token': token,
                'fields': 'id,name,url,desc,dateLastActivity'
            }
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
