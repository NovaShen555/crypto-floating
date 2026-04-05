# crypto-floating

基于 Python 的加密货币价格悬浮窗，实时展示来自 [CoinGlass](https://www.coinglass.com/) 的现货价格。
窗口始终置顶，支持鼠标拖动，每秒刷新一次。

![截图](docs/screenshot.png)

---

## 环境要求

- Python 3.9+
- `tkinter`（大多数 Python 发行版自带；Debian/Ubuntu 若缺失可执行 `sudo apt install python3-tk`）
- `requests`

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
# 显示 ETH 价格（默认）
python floating_price.py

# 显示 BTC 价格
python floating_price.py BTC

# 显示任意支持的交易对
python floating_price.py SOL
```

悬浮窗默认出现在屏幕**右上角**。  
点击 **✕** 关闭窗口，或用鼠标将其拖到任意位置。

调试模式（显示详细日志）：

```bash
python floating_price.py -v
```

## 窗口布局

```
ETH                        ✕
          $3,512.47
             ▲ 1.23%
```

| 元素 | 说明 |
|------|------|
| 交易对符号 | 代币名称（青色） |
| 价格 | 最新现货价格（美元），每秒更新 |
| 涨跌幅 | 24 小时价格变化百分比（上涨绿色 ▲ / 下跌红色 ▼） |

## 数据来源

价格数据来自以下接口：

```
https://fapi.coinglass.com/api/coin/v2/info?symbol=<交易对符号>
```

