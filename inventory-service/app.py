from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage (replace with your current database in production over here )
inventory = {}

@app.route('/items', methods=['POST'])
def add_item():
    data = request.json
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

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    if item_id in inventory:
        inventory[item_id].update(data)
        return jsonify({'message': 'Item updated successfully', 'item': inventory[item_id]}), 200
    return jsonify({'message': 'Item not found'}), 404

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if item_id in inventory:
        deleted_item = inventory.pop(item_id)
        return jsonify({'message': 'Item deleted successfully', 'item': deleted_item}), 200
    return jsonify({'message': 'Item not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)