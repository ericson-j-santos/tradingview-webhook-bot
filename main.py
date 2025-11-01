# ----------------------------------------------- #
# Plugin Name           : TradingView-Webhook-Bot #
# Author Name           : fabston                 #
# File Name             : main.py                 #
# ----------------------------------------------- #

from handler import send_alert
import config
import time
from flask import Flask, request, jsonify

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

app = Flask(__name__)

# Initialize OpenTelemetry if enabled
if config.enable_telemetry:
    # Create a resource with service name
    resource = Resource(attributes={
        "service.name": config.telemetry_service_name
    })
    
    # Set up the tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure the OTLP exporter if endpoint is provided
    if config.telemetry_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=config.telemetry_endpoint)
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    
    # Instrument Flask and requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    
    print(f"[✓] Telemetry enabled for service: {config.telemetry_service_name}")

tracer = trace.get_tracer(__name__)


def get_timestamp():
    timestamp = time.strftime("%Y-%m-%d %X")
    return timestamp


@app.route("/webhook", methods=["POST"])
def webhook():
    whitelisted_ips = ['52.89.214.238', '34.212.75.30', '54.218.53.128', '52.32.178.7']
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Get current span for adding attributes
    current_span = trace.get_current_span()
    current_span.set_attribute("client.ip", client_ip)
    
    if client_ip not in whitelisted_ips:
        current_span.set_attribute("auth.result", "unauthorized")
        current_span.set_attribute("auth.reason", "ip_not_whitelisted")
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        if request.method == "POST":
            data = request.get_json()
            current_span.set_attribute("webhook.key_valid", data.get("key") == config.sec_key)
            
            if data["key"] == config.sec_key:
                print(get_timestamp(), "Alert Received & Sent!")
                current_span.set_attribute("auth.result", "success")
                current_span.set_attribute("alert.message", data.get("msg", "")[:100])  # Limit length
                
                # Add information about which channels are being used
                channels = []
                if "telegram" in data:
                    channels.append("telegram")
                if "discord" in data:
                    channels.append("discord")
                if "slack" in data:
                    channels.append("slack")
                if "teams" in data:
                    channels.append("teams")
                
                current_span.set_attribute("alert.channels", ",".join(channels) if channels else "default")
                
                send_alert(data)
                return jsonify({'message': 'Webhook received successfully'}), 200

            else:
                print("[X]", get_timestamp(), "Alert Received & Refused! (Wrong Key)")
                current_span.set_attribute("auth.result", "unauthorized")
                current_span.set_attribute("auth.reason", "wrong_key")
                return jsonify({'message': 'Unauthorized'}), 401

    except Exception as e:
        print("[X]", get_timestamp(), "Error:\n>", e)
        current_span.set_attribute("error", True)
        current_span.set_attribute("error.message", str(e))
        current_span.record_exception(e)
        return jsonify({'message': 'Error'}), 400


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
