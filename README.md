# MEXC WebSocket Trade Logger

This project provides a WebSocket-based trade logging utility for the MEXC cryptocurrency exchange.

## Features

- Real-time trade execution monitoring via WebSocket
- Secure API authentication with HMAC-SHA256
- JSON Lines logging format for easy parsing
- Comprehensive error handling and logging
- Windows batch launcher included

## Setup

1. Install dependencies:
```bash
pip install aiohttp
```

2. Create configuration file `config.json`:
```json
{
  "api_key": "your_api_key_here",
  "api_secret": "your_api_secret_here"
}
```

3. Create logs directory:
```bash
mkdir logs
```

## Usage

### Run directly:
```bash
python mexc_ws_logger_fixed.py
```

### Run with batch file (Windows):
```bash
start_ws_logger_fixed.bat
```

## Output

- Trade logs: `logs/my_trades_log.jsonl`
- Error logs: `logs/error_log.txt`

## Security

- Keep your `config.json` file secure and never commit it to version control
- API credentials are used only for read-only trade monitoring
- No order placement capabilities included

## Requirements

- Python 3.7+
- aiohttp library
- Valid MEXC API credentials