# Wi-Fi 即時預覽 → 拍照 → 量腳長

此版本符合「先看相機畫面調整位置，再決定何時拍照」。Ameba 串流 H264 1280×720、15 fps 到區域網路；電腦連接 RTSP 後顯示畫面。實際更新率與延遲取決於相機、網路與電腦，不保證 15 fps。

## 1. 本機輸入 Wi-Fi

在專案資料夾執行（已有 .venv-foot 時可用該環境 python.exe）：

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" setup_foot_wifi.py
```

在視窗輸入 Wi-Fi 名稱與密碼，按「保存設定並準備 Arduino 草稿」。不需要在聊天中傳密碼。電腦和 Ameba 需在可互通的同一區網，避免開啟用戶端隔離的訪客網路。

設定保存到 `firmware/ameba_foot_wifi/wifi_secrets.h`，已由 .gitignore 排除。設定另有英文暫存副本供編譯，兩處都含可還原的憑證；請勿分享這些檔案或包含憑證的韌體。上傳不需要 Python 視窗知道 Wi-Fi 密碼。

## 2. Arduino 上傳

開啟設定視窗顯示的英文路徑 `.ino`，這次是 **ameba_foot_wifi.ino**，不是 USB 版 ameba_foot_camera。

- Board：AMB82-MINI。
- Camera Options：實際相機；既有 JXF37 設備沿用 JXF37。
- Show NN Logs：Disable；Erase All Flash Memory：Disable。
- 選實際 CH340 COM 埠。

關閉其他占用 COM 的程式。按住 UART_DOWNLOAD → 按下放開 RESET → 放開 UART_DOWNLOAD → Upload。上傳成功後單獨按 RESET。

開啟 Serial Monitor，115200 baud。連線成功後每 5 秒印出：

```text
READY,AMEBA_FOOT_WIFI
RTSP_URL=rtsp://192.168.x.x:554
```

請使用實際輸出的網址，不要照抄範例 IP。如果一直 WIFI_CONNECTING，檢查 SSID、密碼、訊號與網路型態。Wi-Fi 斷線後本版會提示復原網路並按 RESET，不宣稱自動重新連線成功。

## 3. 開啟即時預覽介面

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" foot_measure_live.py
```

缺少套件時依 `foot10_quickstart.md` 建立環境並安裝 `requirements-foot.txt`。Wi-Fi 介面不需要開啟 COM，Serial Monitor 可用來讀 IP。

1. 在 RTSP 網址欄貼上剛剛的網址（不包含 `RTSP_URL=`）。
2. 按「① 開始／回到預覽」。相機串流啟動後，才會顯示真正的鏡頭畫面。
3. 調整裸腳、10 元硬幣、光線與相機角度。
4. 按「② 拍下目前畫面」。系統保存並凍結你當時看到的那一幀，不再讓新畫面蓋過量測點。
5. 按「手動四點」或「自動量測」，其餘操作同 `foot10_quickstart.md`。
6. 想重拍時按「① 開始／回到預覽」；先前已保存的檔案不會刪除。

也可以透過 `--url rtsp://實際IP:554` 啟動並連線。預覽中不自動錄影或存整段影片，只有按拍照才保存照片。

## 輸出與限制

- 照片保存為 `original.png`，是串流 H264 解碼後的影格。PNG 不再增加有損壓縮，但原始串流本身已有 H264 壓縮。
- 只有凍結照片可以量測；預覽畫面不作為已完成測量。
- 超過 1.5 秒未收到新影格時清除預覽並拒絕拍照；這是電腦端接收新鮮度，不是相機曝光時間保證。網路／解碼緩衝仍可能造成延遲。
- 手動停止串流後，已拍照的照片保留；未拍照的預覽清除。重新連線請按開始預覽。
- **這支 Wi-Fi 韌體不使用之前的 USB ACK／LED 流程，藍綠燈都維持熄滅。** 成功狀態由介面的串流、保存與量測訊息表示，不能把燈號當作證據。
- RTSP 未設密碼，此原型只用於可信任的本機區網，不需路由器開放外網連接埠。
- 硬幣固定假設為新臺幣 10 元、26 mm。透視、鏡頭畸變、腳高度與姿勢限制仍與 USB 版相同。

## 實機驗證狀態

Wi-Fi 韌體已使用本機 AmebaPro2 4.0.9-build20250805、JXF37 設定編譯成功；Python 共 53 項測試通過，包含凍結顯示影格、重拍清除舊結果、拒絕過期畫面及斷線處理。

程式基於本機已安裝 AmebaPro2 的官方 StreamRTSP/VideoOnly 範例。新版已完成實機上傳並接收 1280×720 影像，保存兩次手動量測紀錄；曾發生逾時並以重開介面恢復。相機畫質、長時間穩定性與量測精度仍需更多測試；不將軟體測試視為精度證明。
