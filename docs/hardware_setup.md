# AMB82-MINI 硬體設定與上傳

## 已確認硬體

- 板卡：AMB82-MINI / Ameba Pro2
- 晶片：RTL8735BDM (RTL8735B)
- Windows 序列埠：COM4（CH340）
- 藍燈：`LED_B`，Arduino pin 23 / PF9
- 綠燈：`LED_G`，Arduino pin 24 / PE6

## Arduino IDE 設定

1. 在 `File > Preferences > Additional Boards Manager URLs` 加入：

   `https://github.com/Ameba-AIoT/ameba-arduino-pro2/raw/main/Arduino_package/package_realtek_amebapro2_index.json`

2. 在 Boards Manager 安裝 **Realtek Ameba Boards**。
3. 選擇 `Tools > Board > AmebaPro2 ARM (32-bits) Boards > AMB82-MINI`。
4. 選擇 `Tools > Port > COM4`。
5. 開啟 `firmware/ameba_voice_led/ameba_voice_led.ino`，按 Upload。

若 Upload 失敗：按住 `UART_DOWNLOAD`，按一下 `RESET` 後放開 `UART_DOWNLOAD`，再重試。

## 上傳後驗證

1. 開啟 Arduino Serial Monitor，設定 `115200 baud`、`Newline`。
2. 正常開機會輸出 `READY,AMB82-MINI` 與 LED 狀態。
3. 輸入 `LED,BLUE,ON`，預期回覆 `STATUS,BLUE=ON,GREEN=OFF`，藍燈亮。
4. 輸入 `LED,GREEN,ON`，預期回覆 `STATUS,BLUE=ON,GREEN=ON`，綠燈亮。

### 加分功能測試

輸入 `LED,BLUE,BLINK,3`；藍燈應亮滅三次，最後回覆 `STATUS,BLUE=OFF,...`。
輸入 `LED,GREEN,BLINK,3`；綠燈應亮滅三次，最後回覆 `STATUS,...,GREEN=OFF`。

完成後關閉 Serial Monitor，才可由 Python 開啟 COM4。
