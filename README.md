# TakoNautBot

![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/github/license/fernandolim1/TakoNautBot)

A multifunctional Telegram bot for currency conversion, unit conversion, and OCR-based image translation.

## ✨ Features

- 💱 Currency conversion (e.g., `100 USD to IDR`)
- 📏 Unit conversion (e.g., `170 cm to ft`, `25 c to f`)
- 📖 OCR + translation from images (e.g., reply to an image with `/tlpic hi en`)
- 🌐 Text translation via `/tl <LANGCODE>` (e.g., `/tl en`)
- 🧠 Intelligent routing for messages based on content
- 📅 Scheduled exchange rate updates (OpenExchangeRates)
- ✅ Google Translate v3 support with NMT engine

---

## 📦 Setup

### 1. Clone the repository

```bash
git clone https://github.com/fernandolim1/TakoNautBot.git
cd TakoNautBot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPEN_EXCHANGE_APP_ID=your-open-exchange-api-key
```

### 4. Add your Google Translate v3 credentials

Save your **Google Cloud service account JSON** as:

```
google_api.json
```

> Required for text/image translation via Google Translate v3 API.

### 5. Run the bot

```bash
python main.py
```

---

## ⚙️ Running with systemd (Optional)

To run TakoNautBot in the background on a Linux server using `systemd`:

1. Create a file at `/etc/systemd/system/takonaut.service`:

```ini
[Unit]
Description=TakoNaut Telegram Bot
After=network.target

[Service]
User=yourusername
WorkingDirectory=/home/yourusername/TakoNautBot
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
Environment=GOOGLE_APPLICATION_CREDENTIALS=/home/yourusername/TakoNautBot/google_api.json

[Install]
WantedBy=multi-user.target
```

> Replace `yourusername` and paths with your actual user and directory.

2. Enable and start the service:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable takonaut
sudo systemctl start takonaut
```

3. To check logs:

```bash
journalctl -u takonaut -f
```

---

## 💡 Usage

| Command                        | Description                                              |
|--------------------------------|----------------------------------------------------------|
| `/start`                       | Show welcome and usage tips                              |
| `/help`                        | Show welcome and usage tips                              |
| `/tl <lang>`                   | Translate replied-to text to the target language         |
| `/tlpic <image_lang> <target>`| OCR + translation from image using given language codes  |

Free-form messages supported:

- `100 USD to JPY`
- `25 c to f`
- `3.5 kg to lbs`

---

## ✅ Compatibility

- Python 3.12+
- Tested on Ubuntu 24.04+
- Requires Tesseract-OCR installed (with language data for OCR via `sudo apt install tesseract-ocr-all`)

---

## 🚧 Work In Progress

- `/tlpic auto <target_lang>` – Auto-detect source language in images
- Audio translation support
- PDF translation
- Inline conversion support (`@TakoNautBot 100 USD to IDR`)
- User settings (default language/currency)
- Admin panel for analytics

---

## 🧾 License

[MIT License](LICENSE)