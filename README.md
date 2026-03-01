# Competitive Pricing Tracker

Rakip fiyat takip otomasyonu. E-ticaret sitelerindeki ürün fiyatlarını izler, değişikliklerde bildirim gönderir.

## Özellikler

- Ürün URL'lerinden otomatik fiyat çekme
- Fiyat değişikliği takibi
- Telegram bildirimleri
- JSON/CSV export
- GitHub Actions ile scheduled çalışma

## Kurulum

### 1. Fork & Clone

```bash
git clone https://github.com/erdenizkorkmaz/competitive-pricing-tracker.git
cd competitive-pricing-tracker
```

### 2. Gerekli Ortam Değişkenleri

GitHub Repository Secrets olarak ekle:

| Secret | Açıklama | Örnek |
|--------|----------|-------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `TELEGRAM_CHAT_ID` | Bildirim gönderilecek chat ID | `-1001234567890` |

### 3. Ürün Listesi Düzenleme

`products.json` dosyasını düzenle:

```json
[
  {
    "name": "iPhone 15 Pro",
    "url": "https://example.com/iphone-15-pro",
    "selector": ".price"
  }
]
```

## Çalıştırma

### Lokal

```bash
pip install -r requirements.txt
python tracker.py
```

### GitHub Actions

Workflow her gün saat 09:00'da otomatik çalışır. Manuel tetiklemek için:

GitHub Repo → Actions → Pricing Tracker → Run workflow

## Çıktı

- `prices.json` - Güncel fiyatlar
- `price_history.json` - Fiyat geçmişi
- `price_changes.csv` - Değişiklik raporu

## Lisans

MIT
