from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

orders = {}
USER_SERVICE_URL = "http://user-app.flask-app.svc.cluster.local:80"
INVENTORY_SERVICE_URL = "http://inventory-app.flask-app.svc.cluster.local:80"

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    if not data or 'user_id' not in data or 'items' not in data:
        return jsonify({'message': 'Bad Request: user_id and items are required'}), 400

    user_id = data['user_id']
    items_to_order = data['items']

    # Verify User
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if user_response.status_code != 200:
            return jsonify({'message': 'User not found'}), 404
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'User service unavailable'}), 503

    # Check and Update Inventory
    items_not_found = []
    items_insufficient_quantity = []
    items_update_failed = []
    for item in items_to_order:
        item_id = item['item_id']
        quantity = item['quantity']
        try:
            inventory_response = requests.get(f"{INVENTORY_SERVICE_URL}/items/{item_id}")
            if inventory_response.status_code != 200:
                items_not_found.append(item_id)
            else:
                item_data = inventory_response.json()['item']
                if item_data['quantity'] < quantity:
                    items_insufficient_quantity.append(item_id)
                else:
                    # Update inventory (reduce quantity)
                    update_response = requests.put(f"{INVENTORY_SERVICE_URL}/items/{item_id}", json={'quantity': item_data['quantity'] - quantity})
                    if update_response.status_code != 200:
                        items_update_failed.append(item_id)

        except requests.exceptions.ConnectionError:
            return jsonify({'message': 'Inventory service unavailable'}), 503

    # Create Order if no issues found
    if items_not_found:
        return jsonify({'message': f'Items not found: {items_not_found}'}), 404
    if items_insufficient_quantity:
        return jsonify({'message': f'Insufficient quantity for items: {items_insufficient_quantity}'}), 400
    if items_update_failed:
        return jsonify({'message': f'Failed to update inventory for items: {items_update_failed}'}), 500
    
    order_id = len(orders) + 1
    orders[order_id] = {
        'id': order_id,
        'user_id': user_id,
        'items': items_to_order
    }

    return jsonify({'message': 'Order created successfully', 'order': orders[order_id]}), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify({'orders': list(orders.values())})

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.get(order_id)
    if order:
        return jsonify({'order': order})
    return jsonify({'message': 'Order not found'}), 404

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)