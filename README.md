# 🐙 TakoNautBot

![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/github/license/fernandolim1/TakoNautBot)

A multifunctional Telegram bot for currency conversion, unit conversion, and OCR-based image translation.

[🤖 Try on Telegram » @TakoNautBot](https://t.me/TakoNautBot)

## ✨ Features

- 💱 **Currency Conversion**  
  → `100 USD to IDR`

- 📏 **Unit Conversion**  
  → `170 cm to ft`, `25 c to f`

- 🖼️ **Image Translation (OCR)**  
  → Reply to image with `/tlpic en id`  
  → Supports multiple languages

- 🌐 **Text Translation**  
  → Reply message with `/tl en`

- 📅 **Scheduled Exchange Rate Updates**  
  → Uses OpenExchangeRates API

- 🔠 **Google Translate v3 (NMT)**  
  → High-quality translation engine

- ⏰ **Smart Reminders**  
  → Supports one-time and recurring reminders  
  → Daily / Weekly / Monthly / Yearly at 00:00 GMT+7  
  → Includes pagination with inline buttons  
  → Admin-only in groups


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

```bash
cp .env.example .env
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



## 💡 Usage

| Command                        | Description                                              |
|--------------------------------|----------------------------------------------------------|
| `/help`                        | Show welcome and usage tips                              |
| `/tl <lang>`                   | Translate replied-to text to the target language         |
| `/tlpic <image_lang> <target>`| OCR + translation from image using given language codes  |
| `/remind <time> <message>`         | Set one-time reminder (e.g. `10m`, `1h30m`, `10mins`, `1hour10mins`) (admin-only in groups)    |
| `/remind daily <message>`          | Set daily reminder at 00:00 GMT+7 (admin-only in groups)                                 |
| `/remind weekly <weekday> <msg>`   | Set weekly reminder (e.g. `/remind weekly Monday report`) (admin-only in groups)         |
| `/remind monthly <day> <message>`  | Set monthly reminder on day of month (e.g `/remind monthly 25 payday`) (admin-only in groups)                              | 
| `/remind yearly <day> <month> <msg>`| Set yearly reminder on day/month (e.g. `/remind yearly 11 Jan Happy Birthday`) (admin-only in groups)|
| `/reminder_list`                     | List reminders (paginated with buttons)                            |
| `/reminder_delete <id>`              | Delete a reminder by ID (admin-only in groups)                     |
| `/timezone <tz>`                   | Set your personal timezone (e.g. `Asia/Tokyo`) [List of Timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

Free-form messages supported:

- `100 USD to JPY`
- `25 c to f`
- `3.5 kg to lbs`



## ✅ Compatibility

- Python 3.12+
- Tested on Ubuntu 24.04+
- Requires Tesseract-OCR installed (with language data for OCR via `sudo apt install tesseract-ocr-all`)



## 🚧 Work In Progress

- `/tlpic auto <target_lang>` – Auto-detect source language in images
- Audio translation support
- PDF translation
- Inline conversion support (`@TakoNautBot 100 USD to IDR`)
- User settings (default language/currency)
- Admin panel for analytics


## ☕ Support This Project

If you find this project helpful, consider supporting me:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/O5O61ETJ7G)



## 🧾 License

[MIT License](LICENSE)

---

Made with 🐙 and ☕ by [@vozter](https://github.com/vozter)