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
resource = Resource.create(attributes={"service.name": "order-service"})  # Replace with your service name
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure Jaeger exporter
jaeger_exporter = OTLPSpanExporter(
    endpoint="http://simplest-jaeger-collector.observability.svc.cluster.local:4318/v1/traces",  # Replace with your Jaeger collector endpoint
    insecure=True  # Set to False if using TLS
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument Flask and requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

# Database configuration from environment variables
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

# Replace with your actual service URLs in the Kubernetes cluster
USER_SERVICE_URL = "http://user-app.flask-app.svc.cluster.local:80"
INVENTORY_SERVICE_URL = "http://inventory-app.flask-app.svc.cluster.local:80"

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except mysql.connector.Error as error:
        print("Error connecting to database:", error)
        return None

def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INT NOT NULL,
                item_id INT NOT NULL,
                quantity INT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                PRIMARY KEY (order_id, item_id)
            )
        ''')
        conn.commit()
        cursor.close()
    except mysql.connector.Error as error:
        print("Error creating tables:", error)
    finally:
        if conn and conn.is_connected():
            conn.close()

create_tables()

@app.route('/orders', methods=['POST'])
def create_order():
    with tracer.start_as_current_span("create_order"):
        data = request.json
        if not data or 'user_id' not in data or 'items' not in data:
            return jsonify({'message': 'Bad Request: user_id and items are required'}), 400

        user_id = data['user_id']
        items_to_order = data['items']

        conn = get_db_connection()
        if conn is None:
            return jsonify({'message': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # Verify User
        try:
            with tracer.start_as_current_span("verify_user"):
                user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
                if user_response.status_code != 200:
                    return jsonify({'message': 'User not found'}), 404
        except requests.exceptions.ConnectionError:
            return jsonify({'message': 'User service unavailable'}), 503

        # Check and Update Inventory (with Database Transactions)
        try:
            conn.start_transaction()  # Start a transaction

            for item in items_to_order:
                item_id = item['item_id']
                quantity = item['quantity']

                # Check Inventory
                with tracer.start_as_current_span("check_inventory"):
                    cursor.execute("SELECT quantity FROM items WHERE id = %s FOR UPDATE", (item_id,))
                    result = cursor.fetchone()

                    if result is None:
                        conn.rollback()  # Rollback if item not found
                        return jsonify({'message': f'Item {item_id} not found'}), 404

                    available_quantity = result[0]
                    if available_quantity < quantity:
                        conn.rollback()  # Rollback if insufficient quantity
                        return jsonify({'message': f'Insufficient quantity for item {item_id}'}), 400

                # Update Inventory
                with tracer.start_as_current_span("update_inventory"):
                    new_quantity = available_quantity - quantity
                    cursor.execute("UPDATE items SET quantity = %s WHERE id = %s", (new_quantity, item_id))

            # Create Order
            with tracer.start_as_current_span("insert_order"):
                cursor.execute("INSERT INTO orders (user_id) VALUES (%s)", (user_id,))
                order_id = cursor.lastrowid

            # Add Order Items
            with tracer.start_as_current_span("insert_order_items"):
                for item in items_to_order:
                    cursor.execute("INSERT INTO order_items (order_id, item_id, quantity) VALUES (%s, %s, %s)",
                                   (order_id, item['item_id'], item['quantity']))

            conn.commit()  # Commit the transaction
            print("Transaction Committed")
            # Construct the order object for the response

            order_data = {
                'id': order_id,
                'user_id': user_id,
                'items': items_to_order
            }

            print("Response Data:", {'message': 'Order created successfully', 'order': order_data})  # Debug print
            return jsonify({'message': 'Order created successfully', 'order': order_data}), 201

        except mysql.connector.Error as error:
            print("Error during transaction:", error)
            conn.rollback()  # Rollback on any database error
            return jsonify({'message': 'Failed to create order'}), 500
        except requests.exceptions.ConnectionError:
            return jsonify({'message': 'Inventory or user service unavailable'}), 503
        finally:
            cursor.close()
            conn.close()

@app.route('/orders', methods=['GET'])
def get_orders():
    with tracer.start_as_current_span("get_orders"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM orders")
                orders = cursor.fetchall()

                for order in orders:
                    cursor.execute("""
                        SELECT oi.item_id, oi.quantity, i.name, i.price
                        FROM order_items oi
                        JOIN items i ON oi.item_id = i.id
                        WHERE oi.order_id = %s
                    """, (order['id'],))
                    order_items = cursor.fetchall()
                    order['items'] = [{'item_id': item['item_id'], 'quantity': item['quantity'], 'name': item['name'], 'price': item['price']} for item in order_items]

                return jsonify({'orders': orders}), 200
            except mysql.connector.Error as error:
                print("Error fetching orders:", error)
                return jsonify({'message': 'Failed to fetch orders'}), 500
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'message': 'Database connection failed'}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    with tracer.start_as_current_span("get_order"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                order = cursor.fetchone()

                if order:
                    cursor.execute("""
                        SELECT oi.item_id, oi.quantity, i.name, i.price
                        FROM order_items oi
                        JOIN items i ON oi.item_id = i.id
                        WHERE oi.order_id = %s
                    """, (order_id,))
                    order_items = cursor.fetchall()
                    order['items'] = [{'item_id': item['item_id'], 'quantity': item['quantity'], 'name': item['name'], 'price': item['price']} for item in order_items]
                    return jsonify({'order': order}), 200
                return jsonify({'message': 'Order not found'}), 404
            except mysql.connector.Error as error:
                print("Error fetching order:", error)
                return jsonify({'message': 'Failed to fetch order'}), 500
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'message': 'Database connection failed'}), 500

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)