from flask import Flask, request, jsonify

app = Flask(__name__)

users = {}

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)