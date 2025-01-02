import unittest
from unittest.mock import patch
from app import app  

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter')
    def test_hello(self, MockOTLPSpanExporter):  # Mock the exporter
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "Welcome to the Online Store API Gateway!")

if __name__ == '__main__':
    unittest.main()