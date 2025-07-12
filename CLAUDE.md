# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a MEXC exchange WebSocket trade logging utility for cryptocurrency trading. The project consists of a Python script that connects to MEXC's WebSocket API to monitor and log trade execution events.

## Architecture

The project is built around a single-file asyncio WebSocket client:
- **mexc_ws_logger_fixed.py**: Main script handling MEXC WebSocket connection and trade logging
- **config.json**: Configuration file containing API credentials
- **logs/**: Directory for storing trade logs and error logs
- **start_ws_logger_fixed.bat**: Windows batch script launcher

## Core Components

### WebSocket Connection Flow
1. Load API credentials from `config.json`
2. Generate signed request to obtain `listenKey` from MEXC REST API
3. Establish WebSocket connection using the `listenKey`
4. Listen for `executionReport` events and log trade data

### Authentication
- Uses HMAC-SHA256 signature for API authentication
- Requires API key and secret stored in `config.json`
- Obtains temporary `listenKey` for WebSocket authentication

### Logging System
- Trade events logged to `logs/my_trades_log.jsonl` in JSON Lines format
- Errors logged to `logs/error_log.txt` with timestamps
- Captures order status changes: NEW, FILLED, CANCELED, EXPIRED

## Common Commands

### Setup and Installation
```bash
# Install dependencies
pip install aiohttp

# Create logs directory
mkdir logs
```

### Running the Application
```bash
# Direct Python execution
python mexc_ws_logger_fixed.py

# Windows batch file
start_ws_logger_fixed.bat
```

### Configuration
Edit `config.json` with your MEXC API credentials:
```json
{
  "api_key": "your_api_key_here",
  "api_secret": "your_api_secret_here"
}
```

## Key Files

- `mexc_ws_logger_fixed.py:52-72`: listenKey authentication logic
- `mexc_ws_logger_fixed.py:75-109`: WebSocket connection and message handling
- `mexc_ws_logger_fixed.py:89-103`: Trade execution event parsing
- `config.json`: API credentials (keep secure, not committed to git)

## Error Handling

The application includes comprehensive error handling:
- Connection failures are logged with full stack traces
- Invalid API responses are captured and logged
- WebSocket disconnections are handled gracefully
- Windows async event loop compatibility fix included

## Security Notes

- API credentials are stored in plaintext in `config.json`
- Error logs may contain sensitive debugging information
- The application only reads trade data (no order placement capabilities)