# 10 元硬幣腳長量測：完整執行指南

這版先驗證「已知硬幣直徑 → 換算腳長」是否可行，不需訓練資料集。Ameba 負責拍照及 USB 傳輸，Python 負責量測。程式假設使用者放的是新臺幣 10 元硬幣，不會辨識面額，也不直接輸出品牌鞋碼。

公式：`腳長 mm = 腳長像素 / 硬幣直徑像素 × 26`。例如 520 / 52 × 26 = 260 mm。

26 mm 來源：[中央銀行流通硬幣資料](https://www.cbc.gov.tw/public/data/issue/MONEY/a1/T04.htm)。幾何實作使用 [OpenCV 輪廓、橢圓擬合](https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html)。本指南所列環境與測試為 2026-10-15 本機驗證。

## 1. 需要哪些東西

- AMB82-MINI 與板載相機、可傳資料的 USB 線。
- 一枚 10 元硬幣；不要用其他面額或玩具硬幣。
- 一張夠大、無反光、無圖案的純色墊子，建議藍色，與腳和硬幣顏色有差異。
- 固定相機的支架、均勻光線，以及直尺或可靠的腳長量測工具。
- Windows、Arduino IDE 與 Python 3.10 以上。本次使用 Python 3.12。

## 2. 檔案位置

| 檔案 | 用途 |
|---|---|
| `firmware/ameba_foot_camera/ameba_foot_camera.ino` | 新板端相機韌體，與人臉韌體分開 |
| `foot_measure.py` | 桌面介面與結果保存 |
| `foot_geometry.py` | 自動分割、手動四點與比例換算 |
| `foot_serial.py` | FOOT10 串列協定、JPEG 校驗與 LED 確認 |
| `requirements-foot.txt` | 本次專用 Python 套件 |
| `prepare_foot_arduino.ps1` | 把 Arduino 草稿複製到英文暫存路徑，避開舊工具中文路徑問題 |
| `test_foot_measure.py` | 合成影像、模擬串列與 GUI 測試 |

舊 `main.py`、`gui.py`、`receive_faces.py` 是人臉功能，不適用這支新韌體。

## 3. 上傳 Arduino 韌體

在本專案 PowerShell 執行：

```powershell
Set-Location 'C:\Users\Jessie\Desktop\師大\class\物聯網\ameba'
powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare_foot_arduino.ps1
```

這只執行本次腳本，不修改系統的執行原則。它會輸出一個英文暫存路徑，請使用 Arduino IDE 開啟輸出的 `ameba_foot_camera.ino`。不要打開舊人臉或語音 `.ino`。若之後修改工作區的程式，重新執行腳本取得最新副本。

Arduino IDE 設定：

- Board：**AMB82-MINI**，使用已安裝的 Realtek AmebaPro2 套件。本次編譯版本為 `4.0.9-build20250805`。
- Camera Options：選實際相機感測器。沿用本專案既有 JXF37 的板子選 **JXF37**；換過感測器時不能照抄。
- Show NN Logs：**Disable**。此程式沒有載入人臉或物件偵測模型。
- NN Model Load From：可保留 **Flash**。
- Erase All Flash Memory：**Disable**。
- Port：選當次顯示的 CH340 COM 埠。

關閉 Python GUI、接收程式及 Serial Monitor。按住 `UART_DOWNLOAD`，按一下並放開 `RESET`，再放開 `UART_DOWNLOAD`，然後按 IDE 的 Upload。看到上傳成功後，單獨按一下 `RESET` 啟動相機。

可以暫時開 Serial Monitor（115200 baud、Newline）確認：

```text
READY,AMEBA_FOOT10
STATUS,SOURCE=AMEBA,MODE=FOOT10,TX=0,RX_ID=0,RESULT_ID=0,BLUE=OFF,GREEN=OFF,BUSY=OFF
```

`READY` 可能在開啟監控前已印過，之後仍會每秒回傳 STATUS。看到 FOOT10 狀態代表韌體正在跑；真正相機能否出圖要由拍攝確認。接著**關閉 Serial Monitor**。不要在文字監控視窗手動送 CAPTURE，否則它會顯示 JPEG 二進位亂碼。

若只想用命令列驗證編譯，可執行下列命令；它固定以 JXF37 編譯，不燒錄：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare_foot_arduino.ps1 -Compile
```

如果 Arduino 工具報 `locale::facet`，可完全關閉 IDE，再從設定 `$env:LANG='C'; $env:LC_ALL='C'` 的 PowerShell 啟動 IDE，或先使用上述 Compile 指令確認。不同套件版本的工具行為可能不同。

## 4. 建立獨立 Python 環境

在專案資料夾執行；不需要安裝語音套件、不需要變動現有環境：

```powershell
Set-Location 'C:\Users\Jessie\Desktop\師大\class\物聯網\ameba'
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv-foot
.\.venv-foot\Scripts\python.exe -m pip install -r requirements-foot.txt
.\.venv-foot\Scripts\python.exe -c "import cv2, numpy, PIL, serial, tkinter; print('FOOT10 dependencies OK')"
```

第一行 Python 路徑已在本機確認存在。如果換電腦，可改成可用的 `py -3.12 -m venv .venv-foot`。若 `.venv-foot` 已存在且可以使用，只需安裝套件與檢查，不需重新建立。套件安裝需要網路；程式執行本身不需要網路。

預期最後顯示 `FOOT10 dependencies OK`。

## 5. 先測介面，再接硬體

先啟動合成示範，確認介面與換算能跑：

```powershell
.\.venv-foot\Scripts\python.exe foot_measure.py --demo
```

示範只有橢圓與圓形，**不是實際腳部或硬幣，也不是硬體精度證據**。按「手動四點」，依序選圓形左右兩端、橢圓上端與下端，結果應約 260 mm；點選誤差會影響結果。自動模式對合成圖的像素邊緣估計可能略有差異，不應期待數值完全相同。

關閉示範後，列出實際 COM 埠：

```powershell
.\.venv-foot\Scripts\python.exe -m serial.tools.list_ports
.\.venv-foot\Scripts\python.exe foot_measure.py
```

介面會優先選唯一的 CH340 裝置。若沒有自動選中，在上方選擇 COM 埠；也可以指定：

```powershell
.\.venv-foot\Scripts\python.exe foot_measure.py --port COM3
```

**COM3 只是例子，請換成實際埠號。** 不要同時開舊 GUI、Arduino Serial Monitor 或其他串列程式。

## 6. 拍攝擺法

1. 相機固定在正上方，盡量垂直朝向地面；讓腳與硬幣都靠近畫面中央。
2. 純色墊子填滿整張畫面，四周邊緣也要是墊子。拿掉其他物品、文字、圓形圖案。
3. 一隻裸腳平放、自然承重，腳趾伸直，不穿鞋襪；腳跟和最長腳趾必須看得清楚。腳的長方向可沿影像較長的一邊，增加像素。
4. 10 元硬幣平放在同一張墊子上、靠近腳但不要接觸或被陰影遮住，避免硬幣邊緣反光。
5. 若俯拍時小腿遮住腳跟，請調整姿勢／相機位置；不能靠猜測被遮住的腳跟。自動輪廓若包含小腿，可在看得清腳跟時使用手動模式。
6. 不要只為了塞入畫面而移得很遠。程式要求硬幣至少 30 像素，低於 60 像素會提醒精度敏感。30 是最低操作門檻，不是精度保證。
7. 按「① 拍攝一張」，等畫面完成。解析度為 1280×720、USB 為 115200 baud；傳輸可能需要數秒到數十秒，這不是即時影片。

畫面不理想就調整後重新拍攝。硬幣與腳的輪廓都應清晰，地面應平整。

## 7. 今天建議先用手動四點

這樣可以先把「比例換算」和「自動輪廓分割」的誤差分開。

1. 按「② 手動四點」。
2. 第 1 點：硬幣外圓的一端。
3. 第 2 點：**通過圓心**的對側外圓，必須是直徑，不是隨意的弦。不要選到內圈、文字或陰影。
4. 第 3 點：腳跟最後端。
5. 第 4 點：最長腳趾的最前端，不一定是大拇趾。腳跟到腳趾的線應合理代表長度方向。
6. 硬幣太小看不清楚時，把「檢視比例」改成 100% 或 200%，使用捲軸移動圖片。所有點會換回原圖座標，放大不改變比例計算。
7. 點錯時重新按「手動四點」，四點全部重選。

介面顯示腳長 mm／cm、硬幣像素直徑、mm/px，以及硬幣直徑偏差 1 px 對腳長的大約影響。後者不是完整量測不確定度或信賴區間。

用直尺或腳長量測工具取得參考值，填入「實測腳長 mm」，例如 26 cm 要填 **260**。檢查標記線後勾選底部確認，再按「③ 確認並儲存」。

## 8. 再試自動量測

按「② 自動量測」。程式以影像邊緣估計背景色、分離前景，擬合硬幣橢圓，並計算最大腳部候選輪廓沿主軸的投影長度。

- 硬幣輪廓為黃色，腳部候選輪廓及長度線為綠色。
- 不使用深度學習，所以它不知道一個前景物體是不是真的腳。請檢查是否選中陰影、褲管或其他物品。
- 「背景差異門檻」預設 40。若陰影也被分出來，可嘗試增加；若腳／硬幣漏掉，可降低，但應優先改善光線與背景。
- 找到多個圓、找不到唯一腳部、硬幣太小／太扁、輪廓碰到邊界，會拒絕給出結果。
- 自動「輪廓最大寬」只是該主軸下的橫向投影範圍，不是經解剖定位的足寬。
- 自動量測與手動腳跟—腳趾直線定義不同，應分開記錄與比較。

## 9. 輸出內容與 LED

結果預設儲存在 `foot_captures/<UTC時間_識別碼>/`：

```text
original.jpg                 Ameba 傳來的原始 JPEG（拍攝完成即存檔）
capture.json                 相機來源、傳輸編號與當時板端接收回覆
measurement_<ID>.png         加上輪廓／點選線與腳長的圖
measurement_<ID>.json        長度、比例、方法、警告、參考值與誤差
measurement_<ID>_mask.png    自動模式的前景遮罩
measurement_<ID>.board.json 保存量測後收到的板端狀態（有成功確認時）
```

開啟本機圖片時會保存 `original.png` 工作副本，JSON 記錄原始檔案路徑。每次按儲存會建立不同的 measurement 檔，不覆蓋前一次量測。沒有輸入實測長度時，不會捏造誤差值。JSON 的 `shoe_size` 為 null。

| 燈號 | 這支新韌體的意義 |
|---|---|
| 藍燈約 3 秒 | 電腦已完整解碼、保存原圖並回傳正確 ACK，板端已接受 |
| 綠燈約 5 秒 | 電腦端量測經使用者確認並保存，板端收到相符 RESULT |
| 拍攝開始 | 清除上一次燈號及確認狀態 |

這與舊人臉版本的綠燈語義不同：**板端不偵測腳或硬幣，綠燈不表示量測準確或鞋碼已確認**。離線照片不控制硬體。介面說明的是收到 STATUS 當時的 GPIO 回報，不保證燈現在仍亮。

## 10. 如何判斷機制可不可行

建議先拍同一隻腳 5 次，每次重新擺放硬幣與腳，先用手動四點，輸入同一套實體量測方法取得的參考腳長。再對同一批照片使用自動模式。

比較每張 `measurement_*.json` 的：

- `foot_length_mm`：估計腳長。
- `actual_foot_length_mm`：輸入的參考值。
- `signed_error_mm`：估計值減參考值。
- `absolute_error_mm`：誤差絕對值。
- `mode`：manual 或 auto。

先自訂可接受門檻（例如 5 mm 僅作今日原型目標，並非已達成的精度），觀察平均誤差和重複量測差異。先確認手動模式合理，再評估自動模式是否增加誤差。不要只拿一次很接近的結果就宣布成功。

限制：本版沒有鏡頭畸變校正、透視矯正、深度補償；腳有高度，並非與硬幣表面完全共平面。硬幣即使看起來接近圓形，也不能證明整個畫面尺度一致。測量遠端端點、陰影、鏡頭邊緣及姿勢都可能造成系統誤差。這些需後續用校正板與實測驗證。

## 11. 常見問題

| 現象 | 處理方式 |
|---|---|
| 找不到 COM | 使用可傳資料 USB 線，確認 CH340 裝置、按 RESET、更新埠清單 |
| COM 存取被拒 | 關閉 Serial Monitor、舊 Python GUI 與其他占用程式 |
| 提示不是 FOOT10 | 板上仍是人臉／語音韌體；重新上傳 ameba_foot_camera |
| CAPTURE 長時間逾時 | 按 RESET，確認相機排線、感測器設定；SDK 取像可能卡住，不能靠重試取代重啟 |
| JPEG_SIZE | 畫面 JPEG 超過 512 KiB 上限；先減少背景細節或調整影像品質再重編譯 |
| 自動找不到硬幣／腳 | 用純色墊子填滿畫面、改善光線，或直接手動四點 |
| 腳跟看不到 | 調整構圖或姿勢後重拍，不要猜端點 |
| 存檔後綠燈未確認 | 量測檔可能已保存；檢查訊息及 USB，不把檔案成功當作板端確認 |

## 12. 驗證狀態

此版本已用本機 AmebaPro2 4.0.9-build20250805、JXF37、NN Logs Disable 編譯成功：4,788,224 bytes（28%）。使用英文暫存路徑，未修改已安裝 SDK。

Python 測試涵蓋手動換算、旋轉合成輪廓、無硬幣／多硬幣／變形硬幣拒絕、損毀 JPEG、分段 USB、接收／量測確認、GUI 放大捲動後座標換算與新照片清除舊結果。

本次 13 項新增測試及整個專案共 49 項測試全部通過；已檢查 [介面預覽](foot10_gui_preview.png)，圖中只有合成幾何物件。工作區韌體與編譯副本的 SHA256 相同：`F049A78A6721DA9CB58B2B0B0496992C8C2A5522F58D1C77BE2BDDB6498FECD1`。

**尚未燒錄本版到實體板子，尚未取得真實腳部照片或證明毫米精度。** 合成圖和模擬串列測試不代表實體 LED／相機已通過驗收。

執行測試：

```powershell
.\.venv-foot\Scripts\python.exe -B -m unittest -v test_foot_measure
```
