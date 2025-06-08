"""
📧 Email Service for RaqibTech Customer Support System
Handles welcome emails for new registrations and order confirmation emails
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import logging
from jinja2 import Template
import json

logger = logging.getLogger(__name__)

class EmailService:
    """📧 Email service for customer notifications"""

    def __init__(self):
        """Initialize email service with SMTP configuration"""
        # Email configuration - can be set via environment variables
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = os.getenv('SMTP_PORT')
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
        self.from_name = os.getenv('FROM_NAME')

        # Email templates
        self.welcome_template = self._get_welcome_template()
        self.order_confirmation_template = self._get_order_confirmation_template()

    def _get_welcome_template(self) -> str:
        """Get welcome email template with brand identity and logo"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to raqibtech!</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
                /* Mobile-First Reset and Base Styles */
        body, table, td, a {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }

        body, html {
            margin: 0;
            padding: 0;
            width: 100% !important;
            font-family: Arial, sans-serif;
            line-height: 1.4;
            color: #333;
            background-color: #f4f4f4;
        }

        /* Mobile-First Container */
        .container {
            width: 100% !important;
            margin: 0 auto;
            background-color: #ffffff;
            border-collapse: collapse;
        }

                /* Mobile-First Header */
        .header {
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }

        .logo {
            width: 60px;
            height: 60px;
            margin: 0 auto 15px;
            background: rgba(255,255,255,0.15);
            border-radius: 50%;
            display: table-cell;
            vertical-align: middle;
            text-align: center;
            font-size: 24px;
            border: 2px solid rgba(255,255,255,0.2);
            color: white;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }

        .brand-name {
            font-size: 28px;
            font-weight: bold;
            margin: 15px 0 8px 0;
            color: white;
        }

        .tagline {
            font-size: 14px;
            margin: 0;
            color: rgba(255,255,255,0.9);
        }

        /* Welcome Section */
        .welcome-section {
            padding: 40px 30px;
            text-align: center;
        }

        .welcome-title {
            font-size: 2rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 16px;
            line-height: 1.2;
        }

        .welcome-subtitle {
            font-size: 1.1rem;
            color: #7f8c8d;
            margin-bottom: 30px;
            line-height: 1.5;
        }

        /* Account Card */
        .account-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 16px;
            padding: 25px;
            margin: 30px 0;
            border: 1px solid #dee2e6;
            position: relative;
        }

        .account-card::before {
            content: '👤';
            position: absolute;
            top: -12px;
            left: 25px;
            background: #2ECC71;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            border: 3px solid white;
        }

        .account-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            margin-top: 10px;
        }

        .account-details {
            display: grid;
            gap: 12px;
            text-align: left;
        }

        .account-detail {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }

        .account-detail:last-child {
            border-bottom: none;
        }

        .detail-label {
            font-weight: 500;
            color: #7f8c8d;
        }

        .detail-value {
            font-weight: 600;
            color: #2c3e50;
        }

        .tier-badge {
            display: inline-block;
            background: linear-gradient(135deg, #cd7f32 0%, #b8860b 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 10px 0;
        }

                .contact-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .benefits {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .benefit-item {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }

                .benefit-icon {
            font-size: 1.2em;
            margin-right: 10px;
        }

        .tier-progression {
            background: linear-gradient(90deg, #cd7f32 25%, #c0c0c0 50%, #ffd700 75%, #e5e4e2 100%);
            height: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }

                .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
            color: white;
            text-decoration: none;
            padding: 12px 25px;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }

        /* Benefits Section */
        .benefits-section {
            background: #f8f9fa;
            padding: 30px;
            margin: 0;
        }

        .benefits-title {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 25px;
        }

        .benefits-grid {
            display: grid;
            gap: 16px;
        }

        .benefit-item {
            display: flex;
            align-items: center;
            background: white;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .benefit-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(46, 204, 113, 0.15);
            border-color: #2ECC71;
        }

        .benefit-icon {
            font-size: 1.5rem;
            margin-right: 16px;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #2ECC71, #27AE60);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .benefit-text {
            font-weight: 500;
            color: #2c3e50;
            line-height: 1.4;
        }

        /* Tier Progression */
        .tier-section {
            padding: 30px;
            text-align: center;
        }

        .tier-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
        }

        .tier-subtitle {
            color: #7f8c8d;
            margin-bottom: 25px;
        }

        .tier-progress {
            background: #e9ecef;
            height: 12px;
            border-radius: 20px;
            margin: 20px 0;
            overflow: hidden;
            position: relative;
        }

        .tier-progress::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 25%;
            background: linear-gradient(90deg, #cd7f32 0%, #c0c0c0 25%, #ffd700 75%, #e5e4e2 100%);
            border-radius: 20px;
            animation: progressFill 2s ease-out;
        }

        .tier-list {
            display: grid;
            gap: 12px;
            text-align: left;
            margin: 25px 0;
        }

        .tier-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: white;
            border-radius: 10px;
            border: 1px solid #e9ecef;
            font-size: 0.9rem;
        }

        .tier-item.current {
            background: linear-gradient(135deg, #2ECC71, #27AE60);
            color: white;
            border-color: #2ECC71;
            transform: scale(1.02);
        }

        .tier-icon {
            margin-right: 12px;
            font-size: 1.1rem;
        }

        /* CTA Section */
        .cta-section {
            padding: 40px 30px;
            text-align: center;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }

        .cta-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 20px;
        }

        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
            color: white;
            text-decoration: none;
            padding: 16px 40px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
            box-shadow: 0 8px 25px rgba(46, 204, 113, 0.3);
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            text-transform: uppercase;
        }

        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(46, 204, 113, 0.4);
            background: linear-gradient(135deg, #27AE60 0%, #229954 100%);
        }

        /* Support Section */
        .support-section {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }

        .support-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 20px;
        }

        .support-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }

        .support-item {
            text-align: center;
        }

        .support-icon {
            font-size: 2rem;
            margin-bottom: 10px;
            display: block;
        }

        .support-label {
            font-size: 0.85rem;
            opacity: 0.8;
            margin-bottom: 4px;
        }

        .support-value {
            font-weight: 600;
            font-size: 0.9rem;
        }

        /* Footer */
        .footer {
            background: #34495e;
            color: white;
            padding: 25px 30px;
            text-align: center;
            font-size: 0.85rem;
        }

        .social-links {
            margin: 15px 0;
        }

        .social-links a {
            color: #2ECC71;
            text-decoration: none;
            margin: 0 10px;
            font-weight: 500;
        }

        .footer-note {
            opacity: 0.7;
            margin-top: 15px;
            line-height: 1.4;
        }

        /* Animations */
        @keyframes float {
            0% { transform: translateX(-100px) translateY(-100px); }
            100% { transform: translateX(100px) translateY(100px); }
        }

        @keyframes progressFill {
            0% { width: 0%; }
            100% { width: 25%; }
        }

        /* Desktop Styles */
        @media only screen and (min-width: 600px) {
            .container {
                max-width: 600px !important;
                margin: 20px auto !important;
                border-radius: 16px !important;
                box-shadow: 0 10px 30px rgba(46, 204, 113, 0.15) !important;
                border: 1px solid rgba(46, 204, 113, 0.1) !important;
            }

            .brand-name {
                font-size: 32px !important;
            }

            .logo {
                width: 80px !important;
                height: 80px !important;
                font-size: 32px !important;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%); position: relative;">
            <tr>
                <td align="center" style="padding: 30px 20px; position: relative; background-image: radial-gradient(circle at top right, rgba(255,255,255,0.1) 0%, transparent 50%), radial-gradient(circle at bottom left, rgba(255,255,255,0.05) 0%, transparent 50%);">
                    <div class="logo">🎧</div>
                    <div class="brand-name">raqibtech</div>
                    <div class="tagline">Nigeria's Premier E-commerce Platform</div>
                </td>
            </tr>
        </table>

                <!-- Welcome Section -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td style="padding: 20px;">
                    <h2 style="font-size: 24px; margin: 0 0 15px 0; text-align: center; color: #2c3e50;">Welcome to raqibtech, {{ customer_name }}! 🎉</h2>

                    <p style="margin: 0 0 20px 0; text-align: center; font-size: 16px; line-height: 1.5;">Thank you for joining our community of over <strong>15,000+ satisfied customers</strong> across Nigeria. Your account has been successfully created!</p>

                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #e3f2fd; border-radius: 8px; margin: 20px 0;">
                        <tr>
                            <td style="padding: 20px;">
                                <h3 style="margin: 0 0 15px 0; font-size: 18px; color: #2c3e50;">📋 Your Account Details</h3>
                                <p style="margin: 5px 0; font-size: 14px;"><strong>Customer ID:</strong> {{ customer_id }}</p>
                                <p style="margin: 5px 0; font-size: 14px;"><strong>Email:</strong> {{ customer_email }}</p>
                                <p style="margin: 5px 0; font-size: 14px;"><strong>Account Tier:</strong> <span class="tier-badge">{{ account_tier }}</span></p>
                                <p style="margin: 5px 0; font-size: 14px;"><strong>Location:</strong> {{ customer_state }}, {{ customer_lga }}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- Benefits Section -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #f8f9fa; border-radius: 8px; margin: 20px 0;">
            <tr>
                <td style="padding: 20px;">
                    <h3 style="margin: 0 0 20px 0; text-align: center; font-size: 18px; color: #2c3e50;">🎁 Your Membership Benefits</h3>

                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                        <tr><td style="padding: 8px 0; font-size: 14px; line-height: 1.4;"><span style="margin-right: 10px;">✅</span>Personalized product recommendations based on your preferences</td></tr>
                        <tr><td style="padding: 8px 0; font-size: 14px; line-height: 1.4;"><span style="margin-right: 10px;">🚚</span>Fast delivery across all 36 Nigerian states</td></tr>
                        <tr><td style="padding: 8px 0; font-size: 14px; line-height: 1.4;"><span style="margin-right: 10px;">💰</span>Exclusive member-only deals and discounts</td></tr>
                        <tr><td style="padding: 8px 0; font-size: 14px; line-height: 1.4;"><span style="margin-right: 10px;">🔄</span>Easy returns and 24/7 customer support</td></tr>
                        <tr><td style="padding: 8px 0; font-size: 14px; line-height: 1.4;"><span style="margin-right: 10px;">📱</span>Access to our AI-powered shopping assistant</td></tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- Tier Progression -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td style="padding: 20px;">
                    <h3 style="margin: 0 0 15px 0; text-align: center; font-size: 18px; color: #2c3e50;">🏆 Account Tier Progression</h3>
                    <p style="margin: 0 0 15px 0; text-align: center; font-size: 14px;">You're starting as a <strong>{{ account_tier }}</strong> member. Spend more to unlock higher tiers:</p>

                    <div style="background: linear-gradient(90deg, #cd7f32 25%, #c0c0c0 50%, #ffd700 75%, #e5e4e2 100%); height: 8px; border-radius: 4px; margin: 15px 0;"></div>

                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 14px;">
                        <tr><td style="padding: 5px 0;"><strong style="color: #2ECC71;">Bronze:</strong> ₦0 - ₦99,999 (0% discount)</td></tr>
                        <tr><td style="padding: 5px 0;"><strong style="color: #2ECC71;">Silver:</strong> ₦100K - ₦499,999 (5% discount)</td></tr>
                        <tr><td style="padding: 5px 0;"><strong style="color: #2ECC71;">Gold:</strong> ₦500K - ₦1,999,999 (10% discount + Free delivery)</td></tr>
                        <tr><td style="padding: 5px 0;"><strong style="color: #2ECC71;">Platinum:</strong> ₦2M+ (15% discount + Free delivery + Priority support)</td></tr>
                    </table>

                    <div style="text-align: center; margin: 25px 0;">
                        <a href="https://raqibtech.com" style="background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%); color: white; text-decoration: none; padding: 15px 30px; border-radius: 25px; font-weight: bold; font-size: 16px; display: inline-block;">🛍️ Start Shopping Now</a>
                    </div>
                </td>
            </tr>
        </table>

        <!-- Support Section -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #e3f2fd; border-radius: 8px; margin: 20px 0;">
            <tr>
                <td style="padding: 20px;">
                    <h3 style="margin: 0 0 15px 0; text-align: center; font-size: 18px; color: #2c3e50;">📞 Need Help? We're Here for You!</h3>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 14px;">
                        <tr><td style="padding: 3px 0;"><strong>Customer Support:</strong> Available 24/7</td></tr>
                        <tr><td style="padding: 3px 0;"><strong>Phone:</strong> +234 802 596 5922</td></tr>
                        <tr><td style="padding: 3px 0;"><strong>Email:</strong> support@raqibtech.com</td></tr>
                        <tr><td style="padding: 3px 0;"><strong>Live Chat:</strong> Available on our website</td></tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- Footer -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-top: 1px solid #eee; margin-top: 30px;">
            <tr>
                <td style="padding: 20px; text-align: center; font-size: 12px; color: #666;">
                    <p style="margin: 5px 0;">Follow us for exclusive deals and updates:</p>
                    <p style="margin: 10px 0;">🐦 @raqibtechng | 📘 raqibtech nigeria | 📸 @raqibtechng</p>
                    <p style="margin: 10px 0;">&copy; 2025 raqibtech. All rights reserved. | Based in Lagos, Nigeria</p>
                    <p style="margin: 15px 0 0 0; font-size: 11px; color: #999; line-height: 1.4;">
                        This email was sent to {{ customer_email }} because you created an account with us.<br>
                        If you didn't create this account, please contact us immediately.
                    </p>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
        """

    def _get_order_confirmation_template(self) -> str:
        """Get order confirmation email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Confirmation - RaqibTech</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .header { text-align: center; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; }
        .logo { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
        .order-number { background-color: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; font-size: 1.2em; font-weight: bold; }
        .section { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .order-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #eee; }
        .order-item:last-child { border-bottom: none; }
        .item-details { flex: 1; }
        .item-name { font-weight: bold; color: #333; }
        .item-description { color: #666; font-size: 0.9em; }
        .item-price { font-weight: bold; color: #28a745; text-align: right; }
        .total-row { display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1em; color: #333; border-top: 2px solid #28a745; padding-top: 10px; margin-top: 10px; }
        .tier-discount { color: #dc3545; }
        .delivery-info { background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .status-badge { display: inline-block; background-color: #ffc107; color: #333; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; margin: 10px 0; }
        .cta-button { display: inline-block; background-color: #17a2b8; color: white; text-decoration: none; padding: 12px 25px; border-radius: 5px; margin: 10px 5px; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; }
        .support-info { background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🛒 RaqibTech</div>
            <p>Order Confirmation</p>
            <div class="order-number">Order #{{ order_id }}</div>
        </div>

        <h2>Thank you for your order, {{ customer_name }}! 🎉</h2>

        <p>Your order has been successfully placed and is being processed. Here are your order details:</p>

        <div class="section">
            <h3>📦 Order Items</h3>
            {% for item in order_items %}
            <div class="order-item">
                <div class="item-details">
                    <div class="item-name">{{ item.name }}</div>
                    <div class="item-description">Quantity: {{ item.quantity }} | Unit Price: ₦{{ "{:,.2f}".format(item.unit_price) }}</div>
                </div>
                <div class="item-price">₦{{ "{:,.2f}".format(item.subtotal) }}</div>
            </div>
            {% endfor %}

            <div style="margin-top: 20px;">
                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                    <span>Subtotal:</span>
                    <span>₦{{ "{:,.2f}".format(subtotal) }}</span>
                </div>
                {% if discount_amount > 0 %}
                <div style="display: flex; justify-content: space-between; margin: 5px 0;" class="tier-discount">
                    <span>{{ account_tier }} Tier Discount ({{ "{:.0f}".format(discount_percentage) }}%):</span>
                    <span>-₦{{ "{:,.2f}".format(discount_amount) }}</span>
                </div>
                {% endif %}
                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                    <span>Delivery Fee:</span>
                    <span>{% if delivery_fee == 0 %}FREE{% else %}₦{{ "{:,.2f}".format(delivery_fee) }}{% endif %}</span>
                </div>
                <div class="total-row">
                    <span>Total Amount:</span>
                    <span>₦{{ "{:,.2f}".format(total_amount) }}</span>
                </div>
            </div>
        </div>

        <div class="delivery-info">
            <h3>🚚 Delivery Information</h3>
            <p><strong>Delivery Address:</strong></p>
            <p>{{ delivery_address }}</p>
            <p><strong>Estimated Delivery:</strong> {{ estimated_delivery }}</p>
            <p><strong>Payment Method:</strong> {{ payment_method }}</p>
            <p><strong>Status:</strong> <span class="status-badge">{{ order_status }}</span></p>
        </div>

        <div class="section">
            <h3>📱 Track Your Order</h3>
            <p>Your order is currently being processed. You can track its progress using your order number:</p>
            <div style="text-align: center;">
                <a href="https://raqibtech.com/track/{{ order_id }}" class="cta-button">📍 Track Order</a>
                <a href="https://raqibtech.com/orders" class="cta-button">📋 View All Orders</a>
            </div>
        </div>

        <div class="support-info">
            <h3>❓ Need Help?</h3>
            <p>Our customer support team is here to assist you 24/7:</p>
            <p><strong>Phone:</strong> +234 802 596 5922</p>
            <p><strong>Email:</strong> support@raqibtech.com</p>
            <p><strong>Live Chat:</strong> Available on our website</p>
            <p><strong>WhatsApp:</strong> +234 802 596 5922</p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <h3>🌟 Thank You for Choosing RaqibTech!</h3>
            <p>We appreciate your business and look forward to serving you again.</p>
            <a href="https://raqibtech.com" class="cta-button">🛍️ Continue Shopping</a>
        </div>

        <div class="footer">
            <p>Follow us for exclusive deals and updates:</p>
            <p>🐦 Twitter: @RaqibTechNG | 📘 Facebook: RaqibTech Nigeria | 📸 Instagram: @RaqibTechNG</p>
            <p>&copy; 2025 RaqibTech. All rights reserved. | Based in Lagos, Nigeria</p>
            <p style="font-size: 0.8em; color: #999;">
                This email was sent to {{ customer_email }} regarding your order #{{ order_id }}.
                <br>Order confirmation emails are automatically generated for your reference.
            </p>
        </div>
    </div>
</body>
</html>
        """

    def send_email(self, to_email: str, subject: str, html_content: str, attachments: List[str] = None) -> bool:
        """Send an email with HTML content"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Create HTML part
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)

            # Send email
            if not self.smtp_username or not self.smtp_password:
                logger.warning("📧 Email credentials not configured. Email would be sent to: %s", to_email)
                logger.info("📧 Subject: %s", subject)
                return True  # Return True for testing without actual SMTP

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.from_email, to_email, text)

            logger.info("✅ Email sent successfully to %s", to_email)
            return True

        except Exception as e:
            logger.error("❌ Failed to send email to %s: %s", to_email, str(e))
            return False

    def send_welcome_email(self, customer_data: Dict[str, Any]) -> bool:
        """Send welcome email to new customer"""
        try:
            template = Template(self.welcome_template)

            # Calculate estimated delivery based on location
            delivery_days = 2 if customer_data.get('state') in ['Lagos', 'Abuja'] else 3

            html_content = template.render(
                customer_name=customer_data.get('name', ''),
                customer_id=customer_data.get('customer_id', ''),
                customer_email=customer_data.get('email', ''),
                account_tier=customer_data.get('account_tier', 'Bronze'),
                customer_state=customer_data.get('state', ''),
                customer_lga=customer_data.get('lga', ''),
                delivery_days=delivery_days
            )

            subject = f"🎉 Welcome to raqibtech, {customer_data.get('name', 'Customer')}!"

            return self.send_email(
                to_email=customer_data.get('email'),
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error("❌ Failed to send welcome email: %s", str(e))
            return False

    def send_order_confirmation_email(self, order_data: Dict[str, Any]) -> bool:
        """Send order confirmation email to customer"""
        try:
            template = Template(self.order_confirmation_template)

            # Format delivery address
            delivery_address = f"{order_data.get('delivery_state', '')}, {order_data.get('delivery_lga', '')}"
            if order_data.get('delivery_address'):
                delivery_address = f"{order_data.get('delivery_address')}, {delivery_address}"

            # Calculate estimated delivery date
            delivery_days = 2 if order_data.get('delivery_state') in ['Lagos', 'Abuja'] else 3
            estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).strftime('%B %d, %Y')

            html_content = template.render(
                customer_name=order_data.get('customer_name', ''),
                customer_email=order_data.get('customer_email', ''),
                order_id=order_data.get('order_id', ''),
                order_items=order_data.get('items', []),
                subtotal=order_data.get('subtotal', 0),
                discount_amount=order_data.get('discount_amount', 0),
                discount_percentage=order_data.get('discount_percentage', 0),
                delivery_fee=order_data.get('delivery_fee', 0),
                total_amount=order_data.get('total_amount', 0),
                account_tier=order_data.get('account_tier', 'Bronze'),
                delivery_address=delivery_address,
                estimated_delivery=estimated_delivery,
                payment_method=order_data.get('payment_method', 'Pay on Delivery'),
                order_status=order_data.get('order_status', 'Pending')
            )

            subject = f"📦 Order Confirmation #{order_data.get('order_id', '')} - RaqibTech"

            return self.send_email(
                to_email=order_data.get('customer_email'),
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error("❌ Failed to send order confirmation email: %s", str(e))
            return False

    def send_order_status_update_email(self, order_data: Dict[str, Any], new_status: str) -> bool:
        """Send order status update email"""
        try:
            # Simple status update template
            status_messages = {
                'Processing': 'Your order is now being processed and will be shipped soon! 📦',
                'Shipped': 'Great news! Your order has been shipped and is on its way to you! 🚚',
                'Delivered': 'Your order has been successfully delivered! Thank you for shopping with us! 🎉',
                'Returned': 'Your return request has been processed. Refund will be issued shortly. 💰'
            }

            status_message = status_messages.get(new_status, f'Your order status has been updated to: {new_status}')

            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Order Status Update - #{order_data.get('order_id', '')}</h2>
                <p>Hello {order_data.get('customer_name', 'Customer')},</p>
                <p>{status_message}</p>
                <p><strong>Order ID:</strong> {order_data.get('order_id', '')}</p>
                <p><strong>New Status:</strong> {new_status}</p>
                <p>Track your order: <a href="https://raqibtech.com/track/{order_data.get('order_id', '')}">Click here</a></p>
                <p>Thank you for choosing RaqibTech!</p>
            </div>
            """

            subject = f"📋 Order Update #{order_data.get('order_id', '')} - {new_status}"

            return self.send_email(
                to_email=order_data.get('customer_email'),
                subject=subject,
                html_content=html_content
            )

        except Exception as e:
            logger.error("❌ Failed to send order status update email: %s", str(e))
            return False
