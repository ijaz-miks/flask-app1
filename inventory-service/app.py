import os
import mysql.connector
from flask import Flask, request, jsonify
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
resource = Resource.create(attributes={"service.name": "inventory-service"})  # Replace with your service name
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

# Database configuration from environment variables
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "3306")  # Default MySQL port
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except mysql.connector.Error as error:
        print("Error connecting to database:", error)
    return conn

# Create items table if it doesn't exist
def create_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL
            )
        ''')
        conn.commit()
        cursor.close()
    except mysql.connector.Error as error:
        print("Error creating table:", error)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()

create_table()

@app.route('/items', methods=['POST'])
@metrics.summary('add_item_latency_seconds', 'Latency of adding items')
def add_item():
    with tracer.start_as_current_span("add_item"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            data = request.json
            if not data or 'name' not in data or 'quantity' not in data or 'price' not in data:
                return jsonify({'message': 'Bad Request: name, quantity, and price are required'}), 400
            try:
                cursor.execute("INSERT INTO items (name, quantity, price) VALUES (%s, %s, %s)", (data['name'], data['quantity'], data['price']))
                conn.commit()
                item_id = cursor.lastrowid
                cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
                item = cursor.fetchone()
                item_data = {
                    'id': item[0],
                    'name': item[1],
                    'quantity': item[2],
                    'price': item[3]
                }
                return jsonify({'message': 'Item added successfully', 'item': item_data}), 201
            except mysql.connector.Error as error:
                print("Error adding item:", error)
                conn.rollback()
                return jsonify({'message': 'Failed to add item'}), 500
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'message': 'Database connection failed'}), 500

@app.route('/items', methods=['GET'])
def get_items():
    with tracer.start_as_current_span("get_items"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items")
            items = cursor.fetchall()
            cursor.close()
            conn.close()
            item_list = [{'id': item[0], 'name': item[1], 'quantity': item[2], 'price': item[3]} for item in items]
            return jsonify({'items': item_list})
        else:
            return jsonify({'message': 'Database connection failed'}), 500

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    with tracer.start_as_current_span("get_item"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            cursor.close()
            conn.close()
            if item:
                item_data = {'id': item[0], 'name': item[1], 'quantity': item[2], 'price': item[3]}
                return jsonify({'item': item_data})
            return jsonify({'message': 'Item not found'}), 404
        else:
            return jsonify({'message': 'Database connection failed'}), 500

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    with tracer.start_as_current_span("update_item"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            data = request.json
            try:
                cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
                item = cursor.fetchone()
                if item:
                    if not data:
                        return jsonify({'message': 'Bad Request: No data provided for update'}), 400
                    if 'name' in data:
                        cursor.execute("UPDATE items SET name = %s WHERE id = %s", (data['name'], item_id))
                    if 'quantity' in data:
                        cursor.execute("UPDATE items SET quantity = %s WHERE id = %s", (data['quantity'], item_id))
                    if 'price' in data:
                        cursor.execute("UPDATE items SET price = %s WHERE id = %s", (data['price'], item_id))
                    conn.commit()
                    return jsonify({'message': 'Item updated successfully'})
                return jsonify({'message': 'Item not found'}), 404
            except mysql.connector.Error as error:
                print("Error updating item:", error)
                conn.rollback()
                return jsonify({'message': 'Failed to update item'}), 500
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({'message': 'Database connection failed'}), 500

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    with tracer.start_as_current_span("delete_item"):
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
                item = cursor.fetchone()
                if item:
                    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
                    conn.commit()
                    return jsonify({'message': 'Item deleted successfully'})
                return jsonify({'message': 'Item not found'}), 404
            except mysql.connector.Error as error:
                print("Error deleting item:", error)
                conn.rollback()
                return jsonify({'message': 'Failed to delete item'}), 500
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
    app.run(host='0.0.0.0', port=5001)