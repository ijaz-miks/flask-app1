import os
import mysql.connector
from flask import Flask, request, jsonify
import requests
from prometheus_flask_exporter import PrometheusMetrics

# Import OpenTelemetry modules
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Configure tracing
resource = Resource.create(attributes={"service.name": "api-gateway-service"})  # Replace with your service name
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure Jaeger exporter
jaeger_exporter = OTLPSpanExporter(
    endpoint="http://simplest-jaeger-collector.observability.svc.cluster.local:4318/v1/traces",  # Replace with your Jaeger collector endpoint
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument Flask and requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

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
    with tracer.start_as_current_span("login"):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if authenticate_user(username, password):
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/place_order', methods=['POST'])
@metrics.counter(
    'place_order_requests_total', 'Total number of place_order requests',
    labels={'status': lambda r: r.status_code}
)
def place_order():
    with tracer.start_as_current_span("place_order"):
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
            with tracer.start_as_current_span("verify_user"):
                user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
                if user_response.status_code != 200:
                    return jsonify({'message': 'Invalid user'}), 400
        except requests.exceptions.ConnectionError:
            return jsonify({'message': 'User service unavailable'}), 503

        # Create order
        try:
            with tracer.start_as_current_span("create_order"):
                order_response = requests.post(f"{ORDER_SERVICE_URL}/orders", json={'user_id': user_id, 'items': items})
                print(f"Order Service Response: {order_response.status_code}, {order_response.text}") # Debugging
                if order_response.status_code == 201:
                    order_data = order_response.json()
                    if 'order' in order_data:
                        return jsonify({'message': 'Order placed successfully', 'order': order_data['order']}), 201
                    else:
                        return jsonify({'message': 'Failed to place order', 'details': 'Order service returned unexpected response format'}), 500
                else:
                    return jsonify({'message': 'Failed to place order', 'details': order_response.json()}), order_response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'message': 'Order service unavailable'}), 503

@app.route('/items', methods=['GET'])
def get_items():
    with tracer.start_as_current_span("get_items"):
        # Basic authentication
        auth = request.authorization
        if not auth or not authenticate_user(auth.username, auth.password):
            return jsonify({'message': 'Authentication required'}), 401

        try:
            with tracer.start_as_current_span("get_inventory"):
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

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)