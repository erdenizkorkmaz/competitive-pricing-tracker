import json
import os
import re
import csv
import base64
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def load_products():
    """Load products from products.json"""
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_price_history():
    """Load existing price history"""
    if os.path.exists('price_history.json'):
        with open('price_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_price_history(history):
    """Save price history to file"""
    with open('price_history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def extract_price(text):
    """Extract numeric price from text"""
    if not text:
        return None
    # Remove currency symbols and whitespace
    text = text.replace('₺', '').replace('TL', '').replace('$', '').replace('€', '').replace('USD', '').replace('EUR', '')
    text = text.replace('.', '').replace(',', '.')
    # Find numbers
    numbers = re.findall(r'\d+\.?\d*', text)
    if numbers:
        try:
            return float(numbers[0])
        except ValueError:
            return None
    return None

def fetch_price(url, selector=None):
    """Fetch price from URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Check if content is base64 encoded (httpbin specific)
        if '/base64/' in url:
            # Extract base64 part
            b64_part = url.split('/base64/')[-1]
            try:
                decoded = base64.b64decode(b64_part).decode('utf-8')
                price = extract_price(decoded)
                if price:
                    return price, decoded
            except:
                pass
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try common price selectors if none specified
        selectors = [selector] if selector else [
            '.price',
            '.product-price',
            '.current-price',
            '.sale-price',
            '[data-price]',
            '.money',
            '.amount',
            '.product-price-value',
            '.a-price .a-offscreen',
            '.price-current',
            '.discounted-price'
        ]
        
        for sel in selectors:
            if not sel:
                continue
            element = soup.select_one(sel)
            if element:
                price_text = element.get_text(strip=True)
                price = extract_price(price_text)
                if price:
                    return price, price_text
        
        # Fallback: search for price patterns in text
        text = soup.get_text()
        price_patterns = [
            r'(\d+[.,]?\d*)\s*(?:TL|₺|USD|\$|EUR|€)',
            r'(?:Fiyat|Price|Prix|Preis):?\s*(\d+[.,]?\d*)',
            r'(\d{1,3}(?:,\d{3})+\.?\d*)',
            r'(\d{1,3}(?:\.\d{3})+,?\d*)'
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = extract_price(match.group(1))
                if price:
                    return price, match.group(0)
        
        return None, None
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None

def send_telegram_notification(message):
    """Send notification to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not configured")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def save_to_csv(changes):
    """Save price changes to CSV"""
    if not changes:
        return
    
    file_exists = os.path.exists('price_changes.csv')
    with open('price_changes.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Product', 'Old Price', 'New Price', 'Change', 'URL'])
        for change in changes:
            writer.writerow([
                change['date'],
                change['product'],
                change['old_price'],
                change['new_price'],
                change['change'],
                change['url']
            ])

def main():
    print(f"Starting price tracker at {datetime.now()}")
    
    # Load data
    products = load_products()
    history = load_price_history()
    
    current_prices = {}
    changes = []
    
    for product in products:
        name = product['name']
        url = product['url']
        selector = product.get('selector')
        
        print(f"Checking: {name}")
        
        price, price_text = fetch_price(url, selector)
        
        if price is None:
            print(f"  Could not fetch price for {name}")
            continue
        
        current_prices[name] = {
            'price': price,
            'price_text': price_text,
            'url': url,
            'checked_at': datetime.now().isoformat()
        }
        
        # Check for price change
        if name in history:
            old_price = history[name].get('price')
            if old_price and old_price != price:
                change_pct = ((price - old_price) / old_price) * 100
                change_symbol = "📈" if price > old_price else "📉"
                
                change_info = {
                    'date': datetime.now().isoformat(),
                    'product': name,
                    'old_price': old_price,
                    'new_price': price,
                    'change': f"{change_pct:+.1f}%",
                    'url': url
                }
                changes.append(change_info)
                
                # Send notification
                message = f"{change_symbol} <b>Fiyat Değişikliği!</b>\n\n"
                message += f"<b>Ürün:</b> {name}\n"
                message += f"<b>Eski Fiyat:</b> {old_price:,.2f}\n"
                message += f"<b>Yeni Fiyat:</b> {price:,.2f}\n"
                message += f"<b>Değişim:</b> {change_pct:+.1f}%\n"
                message += f"<a href='{url}'>Ürüne Git →</a>"
                
                send_telegram_notification(message)
                print(f"  Price changed: {old_price} → {price} ({change_pct:+.1f}%)")
            else:
                print(f"  Price unchanged: {price}")
        else:
            print(f"  New product tracked: {price}")
    
    # Save results
    save_price_history(current_prices)
    save_to_csv(changes)
    
    # Save current prices summary
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(current_prices, f, indent=2, ensure_ascii=False)
    
    print(f"\nCompleted. Tracked {len(current_prices)} products.")
    print(f"Price changes detected: {len(changes)}")

if __name__ == '__main__':
    main()
