"""
Crypto price floating window.

Fetches real-time price from CoinGlass and displays it as a small,
always-on-top, draggable overlay window.  Updates every second.

Usage:
    python floating_price.py [SYMBOL]

    SYMBOL defaults to ETH if not provided.

Example:
    python floating_price.py BTC
"""

import logging
import sys
import time
import threading

import requests
import tkinter as tk

logger = logging.getLogger(__name__)

API_URL = "https://fapi.coinglass.com/api/coin/v2/info?symbol={symbol}"
# The problem spec requests 1-second updates; raise this value if the API
# starts rate-limiting your requests.
UPDATE_INTERVAL = 1  # seconds
USER_AGENT = "CryptoFloatingWindow/1.0 (+https://github.com/NovaShen555/crypto-floating)"

# ── colour palette ────────────────────────────────────────────────────────────
BG = "#1a1a2e"
FG_SYMBOL = "#00d4ff"
FG_PRICE = "#ffffff"
FG_CHANGE_UP = "#00e676"
FG_CHANGE_DOWN = "#ff5252"
FG_CLOSE = "#555555"


class CryptoFloating:
    """Draggable floating window that shows the latest crypto spot price."""

    def __init__(self, symbol: str = "ETH") -> None:
        self.symbol = symbol.upper()
        self.running = True

        self.root = tk.Tk()
        self.root.overrideredirect(True)   # no title bar / decorations
        self.root.wm_attributes("-topmost", True)  # always on top
        self.root.configure(bg=BG)

        # Semi-transparent window (works on most platforms)
        try:
            self.root.wm_attributes("-alpha", 0.92)
        except tk.TclError:
            pass

        self._build_ui()
        self._enable_drag()

        # Background thread – keeps fetching prices
        self._thread = threading.Thread(target=self._price_loop, daemon=True)
        self._thread.start()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=BG, padx=14, pady=8)
        outer.pack(fill=tk.BOTH, expand=True)

        # Symbol row
        top_row = tk.Frame(outer, bg=BG)
        top_row.pack(fill=tk.X)

        tk.Label(
            top_row,
            text=self.symbol,
            font=("Helvetica", 9, "bold"),
            fg=FG_SYMBOL,
            bg=BG,
        ).pack(side=tk.LEFT)

        close = tk.Label(
            top_row,
            text="✕",
            font=("Helvetica", 8),
            fg=FG_CLOSE,
            bg=BG,
            cursor="hand2",
        )
        close.pack(side=tk.RIGHT)
        close.bind("<Button-1>", lambda _e: self._quit())

        # Price label
        self.price_var = tk.StringVar(value="—")
        tk.Label(
            outer,
            textvariable=self.price_var,
            font=("Helvetica", 18, "bold"),
            fg=FG_PRICE,
            bg=BG,
            width=13,
            anchor="e",
        ).pack()

        # 24 h change label
        self.change_var = tk.StringVar(value="")
        self.change_label = tk.Label(
            outer,
            textvariable=self.change_var,
            font=("Helvetica", 9),
            fg=FG_CHANGE_UP,
            bg=BG,
            anchor="e",
        )
        self.change_label.pack(fill=tk.X)

    # ── drag support ──────────────────────────────────────────────────────────

    def _enable_drag(self) -> None:
        self._drag_x = 0
        self._drag_y = 0
        self.root.bind("<ButtonPress-1>", self._on_press)
        self.root.bind("<B1-Motion>", self._on_drag)

    def _on_press(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── price fetching ────────────────────────────────────────────────────────

    def _fetch(self) -> dict | None:
        """Return a dict with ``price`` and ``change`` keys, or *None* on error."""
        try:
            url = API_URL.format(symbol=self.symbol)
            resp = requests.get(
                url,
                timeout=5,
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
            body = resp.json()
            if str(body.get("code")) == "0" and body.get("data"):
                data = body["data"]
                price = data.get("price")
                change = data.get("priceChangePercent") or data.get("change24h")
                return {
                    "price": float(price) if price is not None else None,
                    "change": float(change) if change is not None else None,
                }
        except requests.RequestException as exc:
            logger.debug("Network error fetching price: %s", exc)
        except (ValueError, KeyError) as exc:
            logger.debug("Unexpected API response: %s", exc)
        except Exception as exc:  # noqa: BLE001 – last-resort catch
            logger.debug("Unexpected error: %s", exc)
        return None

    def _price_loop(self) -> None:
        """Runs on a background thread; updates the UI via ``after``."""
        while self.running:
            result = self._fetch()
            if result and result["price"] is not None:
                price_text = f"${result['price']:,.2f}"
                change = result["change"]
                if change is not None:
                    sign = "▲" if change >= 0 else "▼"
                    change_text = f"{sign} {abs(change):.2f}%"
                    colour = FG_CHANGE_UP if change >= 0 else FG_CHANGE_DOWN
                else:
                    change_text = ""
                    colour = FG_CHANGE_UP

                def _update(pt=price_text, ct=change_text, c=colour):
                    self.price_var.set(pt)
                    self.change_var.set(ct)
                    self.change_label.configure(fg=c)

                self.root.after(0, _update)

            time.sleep(UPDATE_INTERVAL)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def _quit(self) -> None:
        self.running = False
        self.root.destroy()

    def run(self) -> None:
        # Default position: top-right corner of the screen
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        win_w = self.root.winfo_reqwidth()
        self.root.geometry(f"+{screen_w - win_w - 20}+40")
        self.root.mainloop()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "ETH"
    logging.basicConfig(
        level=logging.DEBUG if "--verbose" in sys.argv or "-v" in sys.argv else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    CryptoFloating(symbol).run()
