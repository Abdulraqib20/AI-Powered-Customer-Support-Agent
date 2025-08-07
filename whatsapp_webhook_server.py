#!/usr/bin/env python3
"""
Simple WhatsApp webhook server for testing
"""
from flask import Flask, request, jsonify
from src.whatsapp_handler import WhatsAppBusinessHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize WhatsApp handler
whatsapp_handler = WhatsAppBusinessHandler()

@app.route('/webhook/whatsapp', methods=['GET'])
def verify_webhook():
    """Verify webhook with Meta"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logger.info(f"🔍 Webhook verification request: mode={mode}, token={token}")

    result = whatsapp_handler.verify_webhook(mode, token, challenge)

    if result:
        logger.info("✅ Webhook verification successful")
        return result
    else:
        logger.warning("❌ Webhook verification failed")
        return "Verification failed", 400

@app.route('/webhook/whatsapp', methods=['POST'])
def handle_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.get_json()
        logger.info(f"📱 Received WhatsApp webhook: {data}")

        result = whatsapp_handler.process_webhook_data(data)

        if result.get('success'):
            logger.info(f"✅ Processed {result.get('processed_messages', 0)} messages")
            return jsonify({'status': 'success'}), 200
        else:
            logger.error(f"❌ Webhook processing failed: {result.get('error')}")
            return jsonify({'status': 'error', 'message': result.get('error')}), 500

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'WhatsApp Webhook Server',
        'whatsapp_configured': whatsapp_handler.config.is_configured()
    })

@app.route('/', methods=['GET'])
def home():
    """Home page"""
    return jsonify({
        'message': 'WhatsApp Webhook Server',
        'endpoints': {
            'webhook_verify': '/webhook/whatsapp (GET)',
            'webhook_handle': '/webhook/whatsapp (POST)',
            'health': '/health'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting WhatsApp Webhook Server...")
    print("📋 Available endpoints:")
    print("   GET  /webhook/whatsapp - Webhook verification")
    print("   POST /webhook/whatsapp - Message handling")
    print("   GET  /health - Health check")
    print("   GET  / - API info")
    print("\n🔗 Use with ngrok: ngrok http 5000")

    app.run(host='0.0.0.0', port=5000, debug=True)
