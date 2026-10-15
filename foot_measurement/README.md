# Ameba Wi-Fi 相機：10 元硬幣輔助腳長量測

第二週可操作原型：**即時預覽 → 拍照凍結 → 手動四點／純色背景自動量測 → 保存紀錄**。

操作影片：https://youtu.be/wGCbTN0mmkw

## 執行

需要 AMB82-MINI 相機開發板、Arduino IDE（AmebaPro2 套件）、Python 3.10+（含 tkinter）。在本資料夾開啟終端：

```powershell
python -m venv .venv-foot
.\.venv-foot\Scripts\python.exe -m pip install -r requirements-foot.txt
.\.venv-foot\Scripts\python.exe setup_foot_wifi.py
```

1. 在本機設定視窗輸入 Wi-Fi，保存後在 Arduino IDE 開啟顯示的英文路徑草稿。真實設定檔不納入 Git。
2. 選 AMB82-MINI、實際相機型號（本次為 JXF37）、實際 COM 埠。按住 UART_DOWNLOAD、按放 RESET、放開 UART_DOWNLOAD 後上傳。
3. 上傳後單獨按 RESET，Serial Monitor 設為 115200，複製 `RTSP_URL=` 後的網址。電腦與板子須在可互通區網。
4. 啟動介面，填入網址並開始預覽：

```powershell
.\.venv-foot\Scripts\python.exe foot_measure_live.py
```

5. 按拍照凍結影像，再用手動四點：硬幣直徑兩端、腳跟、最長腳趾。確認後保存，或回到預覽重拍。

完整指南：[Wi-Fi 操作](docs/foot_wifi_quickstart.md)、[量測原理與 USB 備用模式](docs/foot10_quickstart.md)。

## 已完成與限制

- 固定假設新臺幣 10 元硬幣直徑 26 mm，尚未辨識面額；輸出腳長，不直接推薦鞋碼。
- 新增互動拍照／縮放／參數調整、原圖與 JSON 歷史紀錄、逾時拒拍與異常提示。
- 自動模式採背景分割與幾何輪廓，不是足部語意辨識模型。純色背景外可能失敗，須檢查輪廓。
- Wi-Fi 韌體已實機上傳並收到 1280×720 畫面。曾發生串流逾時，可停止後再連線，必要時重開介面；自動重連尚未實作。
- 兩次手動結果為 273.06、259.23 mm；對使用者輸入的 260 mm，偏差分別 +13.06、-0.77 mm。僅是初步紀錄，不代表已達毫米級精度。
- 穿襪、手動點位、硬幣像素過少、透視、鏡頭畸變、腳部高度都可能影響量測。請以裸腳、固定俯拍與尺量對照測試。
- Wi-Fi 版不使用 USB LED ACK，藍綠燈維持熄滅。
- 私人照片、Wi-Fi 設定與本機測試輸出未上傳。

## 測試

```powershell
.\.venv-foot\Scripts\python.exe -B -m unittest test_foot_measure test_foot_live -v
```

此資料夾包含 17 項腳長相關測試；整個開發工作區先前 53 項測試含其他人臉／語音專案，不全屬本資料夾。合成影像與軟體測試不能替代實體量測驗證。

第三週規劃：純色背景與固定相機、裸腳重複測試、相機校正、自動輪廓與可修正端點、斷線重連；目標平均絕對誤差不超過 5 mm，尚待驗證。
