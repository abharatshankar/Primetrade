# Binance USD-M Futures Testnet — CLI trading bot

Small Python 3 CLI that places **MARKET** and **LIMIT** orders on **Binance USD-M Futures Testnet** (`https://testnet.binancefuture.com`), with layered code (client, orders, validators, logging) and file logging.

## Prerequisites

- Python **3.10+** (uses `str | None` style hints)
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with **USDT-M** API key and secret

## Setup

```bash
cd trading_bot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Export credentials (never commit real keys):

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

Optional:

```bash
export BINANCE_FUTURES_BASE_URL="https://testnet.binancefuture.com"  # default
export TRADING_BOT_LOG_DIR="logs"                                      # default
```

## Run

From the `trading_bot` directory (so `bot` is importable):

```bash
python cli.py --help
```

### MARKET order example

```bash
python cli.py \
  --symbol BTCUSDT \
  --side BUY \
  --order-type MARKET \
  --quantity 0.001
```

`--price` must **not** be set for `MARKET` (it is rejected).

### LIMIT order example

```bash
python cli.py \
  --symbol BTCUSDT \
  --side SELL \
  --order-type LIMIT \
  --quantity 0.001 \
  --price 95000
```

`LIMIT` orders use **`timeInForce=GTC`** by default in the API layer.

### Logs

Each run appends to `logs/trading_bot.log` (or `TRADING_BOT_LOG_DIR` / `--log-dir`).

```bash
python cli.py --log-dir ./logs --log-file my_run.log ...
```

## Sample log files

The repository includes **example** log excerpts (anonymized) showing the shape of output after a successful MARKET and LIMIT run:

- `logs/sample_market_order.log`
- `logs/sample_limit_order.log`

After you run real orders with valid keys, your own `trading_bot.log` will contain live request/response lines suitable for submission.

## Project layout

```
trading_bot/
  bot/
    __init__.py
    client.py          # REST + HMAC signing
    orders.py          # Order construction / placement
    validators.py      # Input validation
    logging_config.py
    types.py           # OrderSide / OrderType
  cli.py
  README.md
  requirements.txt
  logs/
    sample_market_order.log
    sample_limit_order.log
```

## Assumptions

- **Testnet only**: default base URL is `https://testnet.binancefuture.com`; the client is built for signed **USDT-M Futures** REST calls (`/fapi/v1/order`).
- **Credentials** come from `BINANCE_API_KEY` and `BINANCE_API_SECRET`; missing values produce a clear error before any network call.
- **Symbol / filters / min notional** follow Binance rules; the app validates shape and positivity of quantity/price but does not duplicate full exchange filter tables.
- **LIMIT** orders require `--price`; **MARKET** orders must not include `--price`.
- Exit codes: `0` success, `2` validation, `3` missing credentials, `4` API/network `BinanceAPIError`, `5` unexpected error.
