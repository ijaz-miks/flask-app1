from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace with your actual service URLs in the Kubernetes cluster
ORDER_SERVICE_URL = "http://order-app.flask-app.svc.cluster.local:80"
USER_SERVICE_URL = "http://user-app.flask-app.svc.cluster.local:80"
INVENTORY_SERVICE_URL = "http://inventory-app.flask-app.svc.cluster.local:80"

# Very basic authentication for demo purposes
registered_users = {
    "user1": "pass1",
    "user2": "pass2"
}

def authenticate_user(username, password):
    return username in registered_users and registered_users[username] == password

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if authenticate_user(username, password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/place_order', methods=['POST'])
def place_order():
    # Basic authentication
    auth = request.authorization
    if not auth or not authenticate_user(auth.username, auth.password):
        return jsonify({'message': 'Authentication required'}), 401

    data = request.json
    user_id = data.get('user_id')
    items = data.get('items')

    if not user_id or not items:
        return jsonify({'message': 'Bad Request: user_id and items are required'}), 400

    # Verify user (Optional, you might want a more robust way to verify logged-in users)
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if user_response.status_code != 200:
            return jsonify({'message': 'Invalid user'}), 400
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'User service unavailable'}), 503

    # Create order
    try:
        order_response = requests.post(f"{ORDER_SERVICE_URL}/orders", json={'user_id': user_id, 'items': items})
        if order_response.status_code == 201:
            return jsonify({'message': 'Order placed successfully', 'order': order_response.json()['order']}), 201
        else:
            return jsonify({'message': 'Failed to place order', 'details': order_response.json()}), order_response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'Order service unavailable'}), 503

@app.route('/items', methods=['GET'])
def get_items():
    # Basic authentication
    auth = request.authorization
    if not auth or not authenticate_user(auth.username, auth.password):
        return jsonify({'message': 'Authentication required'}), 401

    try:
        inventory_response = requests.get(f"{INVENTORY_SERVICE_URL}/items")
        if inventory_response.status_code == 200:
            return jsonify(inventory_response.json()), 200
        else:
            return jsonify({'message': 'Failed to retrieve items', 'details': inventory_response.json()}), inventory_response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'Inventory service unavailable'}), 503

@app.route('/')
def index():
    return "Welcome to the Online Store API Gateway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)