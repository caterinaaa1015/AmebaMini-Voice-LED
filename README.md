> 新增第二週影像專案：[10 元硬幣輔助腳長量測](foot_measurement/README.md)，提供 Ameba Wi-Fi 韌體、Python 即時預覽與量測介面、操作說明及測試。

# Ameba Mini 語音控制 LED

電腦端接收繁體中文語音，僅接受白名單控制語句，再透過 USB Serial 控制 Ameba Mini 的藍、綠 LED。

> 尚未接板時使用模擬模式；模擬顯示不是實體 LED 證據。

## 目前可測試的功能

- 「左邊開燈」→ `LED,BLUE,ON`
- 「右邊開燈」→ `LED,GREEN,ON`
- 「左邊關燈」與「右邊關燈」
- 非控制語句不傳送資料、不改變 LED 狀態
- 模擬通訊中斷的錯誤提示

## 安裝與執行

先在 PyCharm 設定 Python 3.10 以上的 Interpreter，再在終端機執行：

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m unittest -v
py -3.12 main.py
```

沒有開發板時，輸入文字模擬語音，例如 `左邊開燈`、`今天天氣很好`。

測試通訊失敗：

```powershell
py -3.12 main.py --simulate-disconnect
```

測試麥克風：

```powershell
py -3.12 main.py --mic
```

## 接上 Ameba 後

已確認本專案使用 AMB82-MINI (RTL8735BDM)：`LED_B` 是藍燈（pin 23 / PF9），`LED_G` 是綠燈（pin 24 / PE6），Windows 序列埠目前是 COM4。

1. 依照 [硬體上傳步驟](docs/hardware_setup.md) 上傳 `firmware/ameba_voice_led/ameba_voice_led.ino`。
2. 確認 Arduino Serial Monitor 可收到 `STATUS,BLUE=...` 回覆，再關閉 Serial Monitor。
3. 執行 `py -3.12 main.py --mode serial --port COM4 --baudrate 115200`。

若 Windows 裝置管理員中的 COM 編號改變，請以實際編號取代 `COM4`。

## 安全設計

`command.py` 使用白名單完全比對。語音無法辨識、非控制句，或通訊失敗時，主程式不會宣稱 LED 已改變；只有收到 Ameba 的 `STATUS` 回覆才顯示實體狀態。

## Bonus: blink three times and bilingual commands

After uploading the updated Arduino sketch, these commands are supported:

| Chinese | English | Board protocol |
|---|---|---|
| 左邊閃爍三次 | `blink left three times` | `LED,BLUE,BLINK,3` |
| 右邊閃爍三次 | `blink right three times` | `LED,GREEN,BLINK,3` |
| 左邊開燈 | `turn on left light` | `LED,BLUE,ON` |
| 右邊開燈 | `turn on right light` | `LED,GREEN,ON` |

A blink command takes about 1.5 seconds and ends with its target LED off. For English speech recognition, run:

```powershell
py -3.12 main.py --mode serial --port COM4 --mic --language en-US
```

Use the default `--language zh-TW` for Chinese speech recognition.
