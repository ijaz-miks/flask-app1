from flask import Flask, request, jsonify

app = Flask(__name__)

users = {}

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'message': 'Bad Request: name and email are required'}), 400
    user_id = len(users) + 1
    users[user_id] = {
        'id': user_id,
        'name': data['name'],
        'email': data['email']
    }
    return jsonify({'message': 'User created successfully', 'user': users[user_id]}), 201

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({'users': list(users.values())})

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = users.get(user_id)
    if user:
        return jsonify({'user': user})
    return jsonify({'message': 'User not found'}), 404

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    user = users.get(user_id)
    if user:
        if not data:
            return jsonify({'message': 'Bad Request: No data provided for update'}), 400
        if 'name' in data:
            user['name'] = data['name']
        if 'email' in data:
            user['email'] = data['email']
        return jsonify({'message': 'User updated successfully', 'user': user})
    return jsonify({'message': 'User not found'}), 404

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if user_id in users:
        del users[user_id]
        return jsonify({'message': 'User deleted successfully'}), 200
    return jsonify({'message': 'User not found'}), 404

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)