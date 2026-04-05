# crypto-floating

A tiny Python floating window that shows a live crypto spot price fetched from
[CoinGlass](https://www.coinglass.com/).  The window stays on top of all other
windows, is draggable, and refreshes every second.

![screenshot](docs/screenshot.png)

---

## Requirements

- Python 3.9+
- `tkinter` (ships with most Python distributions; on Debian/Ubuntu install
  `python3-tk` if missing)
- `requests`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Show ETH price (default)
python floating_price.py

# Show BTC price
python floating_price.py BTC

# Show any supported symbol
python floating_price.py SOL
```

The floating window appears in the **top-right corner** of the screen.  
Click the **✕** to close it, or drag it anywhere with the mouse.

## Window layout

```
ETH                        ✕
          $3,512.47
             ▲ 1.23%
```

| element | description |
|---------|-------------|
| symbol  | coin ticker (cyan) |
| price   | latest spot price in USD, updated every second |
| change  | 24 h price change percentage (green ▲ / red ▼) |

## Data source

Prices are fetched from:

```
https://fapi.coinglass.com/api/coin/v2/info?symbol=<SYMBOL>
```
