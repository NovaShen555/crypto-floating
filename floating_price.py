"""
加密货币价格悬浮窗。

每秒从 CoinGlass 接口获取实时价格，以小型悬浮窗的形式展示在屏幕上，
窗口始终置顶，支持鼠标拖动。

用法：
    python floating_price.py [交易对符号]

    未指定符号时默认显示 ETH。

示例：
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
# 需求要求每秒更新一次；若接口触发限流，可适当调大此值。
UPDATE_INTERVAL = 1  # 秒
USER_AGENT = "CryptoFloatingWindow/1.0 (+https://github.com/NovaShen555/crypto-floating)"

# ── 颜色配置 ──────────────────────────────────────────────────────────────────
BG = "#1a1a2e"
FG_SYMBOL = "#00d4ff"
FG_PRICE = "#ffffff"
FG_CHANGE_UP = "#00e676"
FG_CHANGE_DOWN = "#ff5252"
FG_CLOSE = "#555555"


class CryptoFloating:
    """可拖动的悬浮窗，实时展示加密货币现货价格。"""

    def __init__(self, symbol: str = "ETH") -> None:
        self.symbol = symbol.upper()
        self.running = True

        self.root = tk.Tk()
        self.root.overrideredirect(True)   # 隐藏标题栏与边框
        self.root.wm_attributes("-topmost", True)  # 始终置顶
        self.root.configure(bg=BG)

        # 半透明效果（大多数平台支持）
        try:
            self.root.wm_attributes("-alpha", 0.92)
        except tk.TclError:
            pass

        self._build_ui()
        self._enable_drag()

        # 后台线程 — 持续拉取价格
        self._thread = threading.Thread(target=self._price_loop, daemon=True)
        self._thread.start()

    # ── 界面构建 ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg=BG, padx=14, pady=8)
        outer.pack(fill=tk.BOTH, expand=True)

        # 顶部行：交易对符号 + 关闭按钮
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

        # 价格标签
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

        # 24 小时涨跌幅标签
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

    # ── 拖动支持 ──────────────────────────────────────────────────────────────

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

    # ── 价格获取 ──────────────────────────────────────────────────────────────

    def _fetch(self) -> dict | None:
        """请求接口并返回包含 ``price``（价格）和 ``change``（涨跌幅）的字典；出错时返回 *None*。"""
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
            logger.debug("网络请求失败: %s", exc)
        except (ValueError, KeyError) as exc:
            logger.debug("接口返回数据异常: %s", exc)
        except Exception as exc:  # noqa: BLE001 – 兜底捕获
            logger.debug("未知错误: %s", exc)
        return None

    def _price_loop(self) -> None:
        """在后台线程中循环运行，通过 ``after`` 将结果推送到 UI 线程。"""
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

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def _quit(self) -> None:
        self.running = False
        self.root.destroy()

    def run(self) -> None:
        # 默认位置：屏幕右上角
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        win_w = self.root.winfo_reqwidth()
        self.root.geometry(f"+{screen_w - win_w - 20}+40")
        self.root.mainloop()


# ── 程序入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "ETH"
    logging.basicConfig(
        level=logging.DEBUG if "--verbose" in sys.argv or "-v" in sys.argv else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    CryptoFloating(symbol).run()
