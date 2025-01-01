from flask import Flask, request, jsonify

app = Flask(__name__)

inventory = {}

@app.route('/items', methods=['POST'])
def add_item():
    data = request.json
    if not data or 'name' not in data or 'quantity' not in data or 'price' not in data:
        return jsonify({'message': 'Bad Request: name, quantity, and price are required'}), 400
    item_id = len(inventory) + 1
    inventory[item_id] = {
        'id': item_id,
        'name': data['name'],
        'quantity': data['quantity'],
        'price': data['price']
    }
    return jsonify({'message': 'Item added successfully', 'item': inventory[item_id]}), 201

@app.route('/items', methods=['GET'])
def get_items():
    return jsonify({'items': list(inventory.values())})

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = inventory.get(item_id)
    if item:
        return jsonify({'item': item})
    return jsonify({'message': 'Item not found'}), 404

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    item = inventory.get(item_id)
    if item:
        if not data:
            return jsonify({'message': 'Bad Request: No data provided for update'}), 400
        if 'name' in data:
            item['name'] = data['name']
        if 'quantity' in data:
            item['quantity'] = data['quantity']
        if 'price' in data:
            item['price'] = data['price']
        return jsonify({'message': 'Item updated successfully', 'item': item})
    return jsonify({'message': 'Item not found'}), 404

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if item_id in inventory:
        del inventory[item_id]
        return jsonify({'message': 'Item deleted successfully'}), 200
    return jsonify({'message': 'Item not found'}), 404

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)