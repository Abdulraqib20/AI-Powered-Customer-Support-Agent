"""
Sophisticated Order Image Generator with Real Emoji Support
Creates beautiful order confirmation images for WhatsApp delivery using real emoji images
"""

import os
import logging
import requests
import re
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import tempfile
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderImageGenerator:
    """Generate beautiful order confirmation images with real emoji support"""

    def __init__(self):
        # Image dimensions
        self.width = 800
        self.height = 1200

        # Enhanced color palette
        self.colors = {
            'bg': '#ffffff',           # Pure white background
            'primary': '#008751',      # Nigerian green
            'secondary': '#f8f9fa',    # Light gray
            'accent': '#007bff',       # Blue accent
            'text_primary': '#1a1a1a', # Darker text for better contrast
            'text_secondary': '#6c757d', # Medium gray
            'success': '#28a745',      # Success green
            'border': '#dee2e6',       # Light border
            'header_bg': '#008751',    # Header background
            'card_bg': '#f8f9fa',      # Card background
            'highlight': '#fff3cd',    # Highlight background
            'shadow': '#00000010',     # Subtle shadow
            'total_bg': '#e8f5e8',     # Total section background
            'footer_bg': '#f1f3f4',    # Footer background
        }

        # Font sizes
        self.font_sizes = {
            'brand_bold': 32,     # Business name (bold)
            'brand': 28,          # Brand name
            'title': 24,          # Title
            'subtitle': 16,       # Subtitle
            'heading': 20,        # Section headings
            'body': 16,           # Body text
            'small': 14,          # Small text
            'large': 18,          # Large body text
            'total': 28,          # Total amount
        }

        # Emoji settings
        self.emoji_size = 24  # Standard emoji size
        self.emoji_cache = {}  # Cache for downloaded emoji images

        # Load fonts
        self.fonts = self._load_fonts()

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load Poppins fonts with fallbacks"""
        fonts = {}

        # Poppins font paths (preferred)
        poppins_paths = [
            # Windows paths for Poppins
            "C:/Windows/Fonts/Poppins-Regular.ttf",
            "C:/Windows/Fonts/Poppins-Bold.ttf",
            "C:/Windows/Fonts/Poppins-SemiBold.ttf",
            # System paths
            "/System/Library/Fonts/Supplemental/Poppins-Regular.ttf",
            "/usr/share/fonts/truetype/poppins/Poppins-Regular.ttf",
        ]

        # Fallback font paths
        fallback_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf"
        ]

        # Try to load Poppins first, then fallback
        all_paths = poppins_paths + fallback_paths

        for size_name, size in self.font_sizes.items():
            font_loaded = False

            # For brand_bold, try to find a bold variant
            if size_name == 'brand_bold':
                bold_paths = [
                    "C:/Windows/Fonts/Poppins-Bold.ttf",
                    "C:/Windows/Fonts/arial.ttf",  # Fallback will be made bold
                ] + fallback_paths

                for font_path in bold_paths:
                    try:
                        if os.path.exists(font_path):
                            fonts[size_name] = ImageFont.truetype(font_path, size)
                            font_loaded = True
                            logger.info(f"✅ Loaded font for {size_name}: {font_path}")
                            break
                    except Exception:
                        continue
            else:
                for font_path in all_paths:
                    try:
                        if os.path.exists(font_path):
                            fonts[size_name] = ImageFont.truetype(font_path, size)
                            font_loaded = True
                            if 'Poppins' in font_path:
                                logger.info(f"✅ Loaded Poppins font for {size_name}")
                            break
                    except Exception:
                        continue

            if not font_loaded:
                try:
                    fonts[size_name] = ImageFont.load_default()
                    logger.warning(f"⚠️ Using default font for {size_name}")
                except Exception:
                    fonts[size_name] = ImageFont.load_default()

        return fonts

    def _get_emoji_unicode(self, emoji: str) -> str:
        """Convert emoji to unicode hex string for Twemoji URL"""
        try:
            # Convert emoji to unicode codepoint(s)
            codepoints = []
            for char in emoji:
                if ord(char) > 127:  # Non-ASCII characters
                    codepoints.append(f"{ord(char):x}")

            if codepoints:
                return "-".join(codepoints)
            return None
        except Exception as e:
            logger.warning(f"Error converting emoji {emoji} to unicode: {e}")
            return None

    def _download_emoji(self, emoji: str, size: int = 72) -> Optional[Image.Image]:
        """Download emoji image from Twemoji CDN"""
        try:
            # Check cache first
            cache_key = f"{emoji}_{size}"
            if cache_key in self.emoji_cache:
                return self.emoji_cache[cache_key]

            # Get unicode representation
            unicode_hex = self._get_emoji_unicode(emoji)
            if not unicode_hex:
                return None

            # Twemoji CDN URL
            url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{unicode_hex}.png"

            # Download the image
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                emoji_image = Image.open(io.BytesIO(response.content))

                # Convert to RGBA if not already
                if emoji_image.mode != 'RGBA':
                    emoji_image = emoji_image.convert('RGBA')

                # Resize to desired size
                emoji_image = emoji_image.resize((size, size), Image.Resampling.LANCZOS)

                # Cache the image
                self.emoji_cache[cache_key] = emoji_image
                return emoji_image
            else:
                return None

        except Exception as e:
            logger.warning(f"Error downloading emoji {emoji}: {e}")
            return None

    def _draw_text_with_emojis(self, draw: ImageDraw.Draw, image: Image.Image,
                              pos: Tuple[int, int], text: str, font: ImageFont.FreeTypeFont,
                              fill: str = 'black', emoji_size: int = None) -> int:
        """Draw text with real emojis inline"""
        if emoji_size is None:
            emoji_size = self.emoji_size

        # Find all emojis in the text
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')

        # If no emojis, draw normally
        if not emoji_pattern.search(text):
            draw.text(pos, text, font=font, fill=fill)
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]  # Return width

        # Split text into parts
        parts = []
        last_end = 0

        for match in emoji_pattern.finditer(text):
            # Add text before emoji
            if match.start() > last_end:
                parts.append(('text', text[last_end:match.start()]))

            # Add emoji
            parts.append(('emoji', match.group()))
            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            parts.append(('text', text[last_end:]))

        # Draw each part
        x_offset = pos[0]
        y_pos = pos[1]

        for part_type, part_text in parts:
            if part_type == 'text':
                if part_text.strip():  # Only draw non-empty text
                    draw.text((x_offset, y_pos), part_text, font=font, fill=fill)
                    bbox = font.getbbox(part_text)
                    x_offset += bbox[2] - bbox[0]
            else:  # emoji
                emoji_img = self._download_emoji(part_text, emoji_size)
                if emoji_img:
                    # Calculate vertical centering
                    font_height = font.size
                    y_offset = y_pos + (font_height - emoji_size) // 2

                    # Paste emoji with proper transparency handling
                    try:
                        image.paste(emoji_img, (x_offset, y_offset), emoji_img)
                    except Exception as e:
                        logger.warning(f"Error pasting emoji {part_text}: {e}")
                        # Fallback: draw the emoji text
                        draw.text((x_offset, y_pos), part_text, font=font, fill=fill)

                x_offset += emoji_size

        return x_offset - pos[0]  # Return total width

    def generate_order_confirmation(self, order_data: Dict[str, Any]) -> Optional[str]:
        """Generate sophisticated order confirmation image with real emojis"""
        try:
            # Create image with white background
            image = Image.new('RGB', (self.width, self.height), self.colors['bg'])
            draw = ImageDraw.Draw(image)

            # Current y position
            y_pos = 0

            # Draw sections
            y_pos = self._draw_header(draw, image, y_pos, order_data)
            y_pos = self._draw_order_info(draw, image, y_pos, order_data)
            y_pos = self._draw_items(draw, image, y_pos, order_data)
            y_pos = self._draw_pricing_breakdown(draw, image, y_pos, order_data)
            y_pos = self._draw_delivery_info(draw, image, y_pos, order_data)
            y_pos = self._draw_footer(draw, image, y_pos, order_data)

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.png',
                delete=False,
                dir=tempfile.gettempdir()
            )

            image.save(temp_file.name, 'PNG', quality=95)
            temp_file.close()

            logger.info(f"✅ Order confirmation image generated: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            logger.error(f"❌ Error generating order confirmation image: {e}")
            return None

    def _draw_header(self, draw: ImageDraw.Draw, image: Image.Image, y_pos: int, order_data: Dict) -> int:
        """Draw stylish header with real shopping cart emoji and bold business name"""
        header_height = 140

        # Draw header background
        draw.rectangle([0, y_pos, self.width, y_pos + header_height],
                      fill=self.colors['header_bg'])

        # Add shadow effect
        draw.rectangle([0, y_pos + header_height, self.width, y_pos + header_height + 3],
                      fill=self.colors['shadow'])

        # Draw header text with emoji
        header_text = "🛒 Order Confirmation"
        header_x = (self.width - 300) // 2  # Approximate width
        self._draw_text_with_emojis(draw, image, (header_x, y_pos + 25),
                                   header_text, self.fonts['title'],
                                   fill='white', emoji_size=32)

        # Bold business name - raqibtech.com
        brand_text = "raqibtech.com"
        brand_width = draw.textlength(brand_text, font=self.fonts['brand_bold'])
        brand_x = (self.width - brand_width) // 2
        draw.text((brand_x, y_pos + 90), brand_text,
                 fill='white', font=self.fonts['brand_bold'])

        return y_pos + header_height + 20

    def _draw_order_info(self, draw: ImageDraw.Draw, image: Image.Image, y_pos: int, order_data: Dict) -> int:
        """Draw order information card with emojis and database customer name"""
        padding = 30
        card_height = 140

        # Draw card background
        draw.rectangle([padding, y_pos, self.width - padding, y_pos + card_height],
                      fill=self.colors['card_bg'])

        # Order ID with emoji
        order_id = order_data.get('order_id', 'N/A')
        order_text = f"📋 Order ID: {order_id}"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos + 20),
                                   order_text, self.fonts['heading'],
                                   fill=self.colors['text_primary'])

        # Date with emoji
        date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        date_text = f"📅 Date: {date_str}"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos + 50),
                                   date_text, self.fonts['body'],
                                   fill=self.colors['text_secondary'])

        # Customer with emoji - using database customer name
        customer_name = order_data.get('customer_name', 'Valued Customer')
        customer_text = f"👤 Customer: {customer_name}"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos + 75),
                                   customer_text, self.fonts['body'],
                                   fill=self.colors['text_secondary'])

        # Status badge
        status = order_data.get('status', 'Pending')
        status_bg_width = 100
        status_bg_height = 25
        status_x = self.width - padding - status_bg_width - 20
        draw.rectangle([status_x, y_pos + 20, status_x + status_bg_width, y_pos + 20 + status_bg_height],
                      fill=self.colors['success'])

        status_text_width = draw.textlength(status, font=self.fonts['small'])
        status_text_x = status_x + (status_bg_width - status_text_width) // 2
        draw.text((status_text_x, y_pos + 25), status,
                 fill='white', font=self.fonts['small'])

        return y_pos + card_height + 20

    def _draw_items(self, draw: ImageDraw.Draw, image: Image.Image, y_pos: int, order_data: Dict) -> int:
        """Draw items section with emojis"""
        padding = 30

        # Section heading with emoji
        items_text = "🛍️ Order Items"
        self._draw_text_with_emojis(draw, image, (padding, y_pos),
                                   items_text, self.fonts['heading'],
                                   fill=self.colors['text_primary'])
        y_pos += 40

        items = order_data.get('items', [])
        if not items:
            no_items_text = "📦 No items found"
            self._draw_text_with_emojis(draw, image, (padding, y_pos),
                                       no_items_text, self.fonts['body'],
                                       fill=self.colors['text_secondary'])
            return y_pos + 40

        for i, item in enumerate(items):
            item_height = 70

            # Alternate background colors
            bg_color = self.colors['card_bg'] if i % 2 == 0 else self.colors['bg']
            draw.rectangle([padding, y_pos, self.width - padding, y_pos + item_height],
                          fill=bg_color)

            # Product name
            product_name = item.get('product_name', 'Product')
            product_text = f"• {product_name}"
            draw.text((padding + 20, y_pos + 15), product_text,
                     fill=self.colors['text_primary'], font=self.fonts['body'])

            # Quantity and price
            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            draw.text((padding + 20, y_pos + 40), f"Qty: {quantity} × ₦{price:,.2f}",
                     fill=self.colors['text_secondary'], font=self.fonts['small'])

            # Subtotal
            subtotal = item.get('subtotal', price * quantity)
            subtotal_text = f"₦{subtotal:,.2f}"
            subtotal_width = draw.textlength(subtotal_text, font=self.fonts['large'])
            draw.text((self.width - padding - subtotal_width - 20, y_pos + 25),
                     subtotal_text, fill=self.colors['text_primary'], font=self.fonts['large'])

            y_pos += item_height

        return y_pos + 20

    def _draw_pricing_breakdown(self, draw: ImageDraw.Draw, image: Image.Image, y_pos: int, order_data: Dict) -> int:
        """Draw comprehensive pricing breakdown with tier discounts"""
        padding = 30

        # Calculate section height based on content
        base_height = 120
        has_tier_discount = order_data.get('tier_discount', 0) > 0 or order_data.get('discount_amount', 0) > 0
        section_height = base_height + (30 if has_tier_discount else 0)

        # Background
        draw.rectangle([padding, y_pos, self.width - padding, y_pos + section_height],
                      fill=self.colors['total_bg'])

        # Title with emoji
        pricing_text = "💰 Pricing Breakdown"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos + 15),
                                   pricing_text, self.fonts['heading'],
                                   fill=self.colors['text_primary'])

        y_pos += 50

        # Subtotal
        subtotal = order_data.get('subtotal', 0)
        draw.text((padding + 20, y_pos), "Subtotal:",
                 fill=self.colors['text_secondary'], font=self.fonts['body'])
        subtotal_text = f"₦{float(subtotal):,.2f}"
        subtotal_width = draw.textlength(subtotal_text, font=self.fonts['body'])
        draw.text((self.width - padding - subtotal_width - 20, y_pos),
                 subtotal_text, fill=self.colors['text_primary'], font=self.fonts['body'])

        y_pos += 25

        # 🎯 FIXED: Add tier discount if it exists
        if has_tier_discount:
            tier_discount = order_data.get('tier_discount', order_data.get('discount_amount', 0))
            # Get tier information
            account_tier = order_data.get('account_tier', order_data.get('customer_tier', 'Bronze'))

            # Calculate discount percentage
            tier_discounts = {'Bronze': 0, 'Silver': 5, 'Gold': 10, 'Platinum': 15}
            discount_percentage = tier_discounts.get(account_tier, 0)

            # Display tier discount
            discount_label = f"{account_tier} Discount ({discount_percentage}%):"
            draw.text((padding + 20, y_pos), discount_label,
                     fill=self.colors['success'], font=self.fonts['body'])  # Green for discount
            discount_text = f"-₦{float(tier_discount):,.2f}"
            discount_width = draw.textlength(discount_text, font=self.fonts['body'])
            draw.text((self.width - padding - discount_width - 20, y_pos),
                     discount_text, fill=self.colors['success'], font=self.fonts['body'])

            y_pos += 25

        # Delivery fee
        delivery_fee = order_data.get('delivery_fee', 0)
        delivery_label = "Delivery Fee:"

        # Check if delivery is free (for Gold/Platinum tiers)
        account_tier = order_data.get('account_tier', order_data.get('customer_tier', 'Bronze'))
        if delivery_fee == 0 and account_tier in ['Gold', 'Platinum']:
            delivery_label = f"Delivery Fee (FREE for {account_tier}):"

        draw.text((padding + 20, y_pos), delivery_label,
                 fill=self.colors['text_secondary'], font=self.fonts['body'])

        if delivery_fee == 0:
            delivery_text = "FREE"
            draw.text((self.width - padding - 60 - 20, y_pos),  # Approximate width of "FREE"
                     delivery_text, fill=self.colors['success'], font=self.fonts['body'])
        else:
            delivery_text = f"₦{float(delivery_fee):,.2f}"
            delivery_width = draw.textlength(delivery_text, font=self.fonts['body'])
            draw.text((self.width - padding - delivery_width - 20, y_pos),
                     delivery_text, fill=self.colors['text_primary'], font=self.fonts['body'])

        y_pos += 35

        # Total with emphasis
        draw.text((padding + 20, y_pos), "TOTAL:",
                 fill=self.colors['text_primary'], font=self.fonts['heading'])
        total_amount = order_data.get('total_amount', 0)
        total_text = f"₦{float(total_amount):,.2f}"
        total_width = draw.textlength(total_text, font=self.fonts['total'])
        draw.text((self.width - padding - total_width - 20, y_pos - 5),
                 total_text, fill=self.colors['primary'], font=self.fonts['total'])

        return y_pos + 60

    def _draw_delivery_info(self, draw: ImageDraw.Draw, image: Image.Image, y_pos: int, order_data: Dict) -> int:
        """Draw delivery information with emojis"""
        padding = 30
        section_height = 120

        # Background
        draw.rectangle([padding, y_pos, self.width - padding, y_pos + section_height],
                      fill=self.colors['card_bg'])

        # Title with emoji
        delivery_text = "🚚 Delivery Information"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos + 15),
                                   delivery_text, self.fonts['heading'],
                                   fill=self.colors['text_primary'])

        y_pos += 50

        # Address with emoji
        delivery_address = order_data.get('delivery_address', 'Address not specified')
        address_text = f"📍 Address: {delivery_address}"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos),
                                   address_text, self.fonts['body'],
                                   fill=self.colors['text_secondary'])

        y_pos += 30

        # Payment with emoji
        payment_method = order_data.get('payment_method', 'Not specified')
        payment_text = f"💳 Payment: {payment_method}"
        self._draw_text_with_emojis(draw, image, (padding + 20, y_pos),
                                   payment_text, self.fonts['body'],
                                   fill=self.colors['text_secondary'])

        return y_pos + 50

    def _draw_footer(self, draw: ImageDraw.Draw, image: Image.Image, y_pos: int, order_data: Dict) -> int:
        """Draw footer with correct support contact details and emojis"""
        padding = 30
        footer_height = 100

        # Background
        draw.rectangle([0, y_pos, self.width, y_pos + footer_height],
                      fill=self.colors['footer_bg'])

        # Thank you message with emoji
        thank_you_text = "🎉 Thank you for choosing raqibtech.com!"
        thank_you_x = (self.width - 400) // 2  # Approximate width
        self._draw_text_with_emojis(draw, image, (thank_you_x, y_pos + 15),
                                   thank_you_text, self.fonts['large'],
                                   fill=self.colors['primary'])

        # Support contact info with correct details
        contact_text = "📞 Phone: +234 802 596 5922 | 📧 Email: support@raqibtech.com"
        contact_x = 30  # Left aligned for better readability
        self._draw_text_with_emojis(draw, image, (contact_x, y_pos + 45),
                                   contact_text, self.fonts['small'],
                                   fill=self.colors['text_secondary'])

        # Additional support options
        additional_text = "💬 WhatsApp: +234 802 596 5922 | 🌐 Live Chat: raqibtech.com"
        self._draw_text_with_emojis(draw, image, (contact_x, y_pos + 65),
                                   additional_text, self.fonts['small'],
                                   fill=self.colors['text_secondary'])

        return y_pos + footer_height

    def cleanup_temp_file(self, file_path: str) -> bool:
        """Clean up temporary image file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up temporary image: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error cleaning up temp file {file_path}: {e}")
            return False

# Global instance
order_image_generator = OrderImageGenerator()

def generate_order_image(order_data: Dict[str, Any]) -> Optional[str]:
    """
    Convenience function to generate order confirmation image

    Args:
        order_data: Dictionary containing order information

    Returns:
        Path to generated image file or None if failed
    """
    return order_image_generator.generate_order_confirmation(order_data)

def cleanup_order_image(file_path: str) -> bool:
    """
    Convenience function to clean up order image file

    Args:
        file_path: Path to image file to clean up

    Returns:
        True if cleaned up successfully, False otherwise
    """
    return order_image_generator.cleanup_temp_file(file_path)
