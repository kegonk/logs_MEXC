# MEXC Private WebSocket Event Logger

A small Python utility for authenticated MEXC account-event monitoring. It obtains a signed user-data listen key, subscribes to the private WebSocket stream, classifies account/order events, and stores raw and normalized records as JSON Lines.

This project is intentionally **read-only from a trading perspective**: it observes private account events and does not contain an order-placement path.

## What this project demonstrates

- authenticated REST requests with HMAC-SHA256 signing;
- private WebSocket subscription handling;
- JSON event parsing and normalization;
- reconnect and ping/pong handling;
- structured JSONL logging;
- signal-aware shutdown;
- separation of raw events, normalized trade events, and connection lifecycle logs.

## Data flow

    config.json
        |
        v
    HMAC-signed REST request
        |
        v
    MEXC user-data listen key
        |
        v
    Private WebSocket stream
        |
        +--> raw event log
        +--> event classification
        +--> normalized account/order event log
        +--> connection lifecycle log

## Logged event categories

The parser distinguishes account changes associated with events such as:

- order placed;
- order canceled;
- order filled;
- trade settled;
- balance changes;
- unknown/unmapped provider events.

The original provider payload is retained alongside normalized fields for later analysis.

## Output

Runtime data is written under the local logs/ directory:

    logs/mexc_working_trades.jsonl
    logs/mexc_working_events.jsonl
    logs/mexc_working_connection.jsonl

## Setup

Create a virtual environment and install the two runtime dependencies:

    python -m venv venv

    # Linux/macOS
    source venv/bin/activate
    pip install websocket-client requests

Create a local config.json file:

    {
      "api_key": "YOUR_MEXC_API_KEY",
      "api_secret": "YOUR_MEXC_API_SECRET"
    }

Keep config.json out of version control.

Run directly:

    python mexc_working_logger.py

Or on Linux:

    ./start_logger.sh

## Security notes

- Never commit config.json or real exchange credentials.
- Prefer API credentials with only the permissions required for monitoring.
- Rotate credentials immediately if they are exposed.
- The repository contains no order-placement function.

## Portfolio context

This is a focused integration utility rather than a full application. It demonstrates working with authenticated third-party APIs, private real-time WebSocket streams, event normalization, connection lifecycle handling, and structured telemetry collection in Python.

For a larger public Python project, see my multi-exchange signal scanner repository.
