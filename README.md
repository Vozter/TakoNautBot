# TakoNautBot

A Telegram bot for currency conversion using Open Exchange Rates API.

## Features
- Fetches and caches exchange rates hourly.
- Converts currencies based on user input.

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/TakoNautBot.git
   cd TakoNautBot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file:
   ```plaintext
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   OPEN_EXCHANGE_APP_ID=your-open-exchange-api-key
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## License
[MIT License](LICENSE)