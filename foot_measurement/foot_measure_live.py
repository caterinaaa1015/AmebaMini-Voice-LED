"""Live Ameba RTSP preview, freeze the displayed frame, then measure."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import tkinter as tk
from tkinter import messagebox, ttk

from foot_geometry import write_png
from foot_live import LiveStream
from foot_measure import FootApp, new_folder


class LiveFootApp(FootApp):
    def __init__(self, root, output, url=""):
        self.stream = None
        self.previewing = False
        self.visible_frame = None
        self.visible_time = 0
        super().__init__(root, output)
        root.title("Ameba · Wi-Fi 即時預覽與腳長量測")
        top = self.port_box.master
        # Hide the USB-only row. Keep existing measurement controls in other rows.
        for child in top.grid_slaves(row=0):
            child.grid_remove()
        self.url = tk.StringVar(value=url)
        ttk.Label(top, text="RTSP 網址").grid(row=0, column=0)
        ttk.Entry(top, textvariable=self.url, width=36).grid(row=0, column=1, columnspan=2)
        controls = [("① 開始／回到預覽", self.start_preview),
                    ("② 拍下目前畫面", self.capture), ("開啟照片", self.open_file)]
        for column, (label, command) in enumerate(controls, 3):
            button = ttk.Button(top, text=label, command=command)
            button.grid(row=0, column=column, padx=3, pady=4)
            self.buttons.append(button)
        ttk.Button(top, text="停止串流", command=self.stop_preview).grid(row=0, column=6)
        for column, (label, command) in enumerate([("自動量測", self.automatic), ("手動四點", self.start_manual)], 3):
            button = ttk.Button(top, text=label, command=command)
            button.grid(row=3, column=column, pady=4)
            self.buttons.append(button)
        self.status.set("先填入 Serial Monitor 顯示的 RTSP 網址，再按開始預覽。此模式不需要 Python 開啟 COM 埠。")
        self.summary.set("預覽中可調整腳與硬幣的位置；拍下目前畫面後，才進行量測。")
        self.live_timer = root.after(80, self.update_preview)

    def start_preview(self):
        if self.busy:
            return
        try:
            if self.stream is None or self.stream.url != self.url.get().strip() or not self.stream.thread.is_alive():
                if self.stream:
                    self.stream.close()
                self.stream = LiveStream(self.url.get())
            self.previewing = True
            self.visible_frame = None
            self.set_image_empty()
            self.status.set("正在連接／接收即時畫面…")
        except ValueError as error:
            messagebox.showerror("RTSP 網址", str(error))

    def set_image_empty(self):
        self.image = self.display = self.result = self.mask = self.frame = self.folder = None
        self.points, self.manual = [], False
        self.confirmed.set(False)
        self.zoom.set("適合視窗")
        self.canvas.delete("all")
        self.summary.set("即時預覽中。將相機垂直朝下，完整拍到腳與 10 元硬幣，再按拍下目前畫面。")

    def update_preview(self):
        if self.closed:
            return
        if self.previewing and self.stream:
            try:
                frame, stamp = self.stream.snapshot()
                if stamp != self.visible_time or self.visible_frame is None:
                    self.visible_frame, self.visible_time = frame, stamp
                    self.display = frame
                    self.redraw()
                    self.status.set("即時預覽中（Wi-Fi 串流可能有延遲）。調整好位置後，按『拍下目前畫面』。")
            except ValueError as error:
                self.visible_frame = None
                self.display = None
                self.canvas.delete("all")
                self.status.set(str(error))
        self.live_timer = self.root.after(80, self.update_preview)

    def capture(self):
        if self.busy:
            return
        if not self.previewing or self.visible_frame is None or time.monotonic() - self.visible_time > 1.5:
            messagebox.showinfo("尚無即時影像", "請先開始預覽，等待清楚的新畫面後再拍照。")
            return
        # Freeze the exact frame last shown to the user, not a later decoder frame.
        frame = self.visible_frame.copy()
        self.previewing = False
        source = {"kind": "ameba_rtsp_decoded_frame", "image": "original.png",
                  "rtsp_url": self.stream.url, "captured_utc": datetime.now(timezone.utc).isoformat(),
                  "note": "Displayed H264 decoded frame; PNG adds no further lossy compression. No USB LED ACK."}
        self.set_image(frame, source)
        try:
            folder = new_folder(self.output)
            write_png(folder / "original.png", frame)
            (folder / "capture.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
            self.folder = folder
            self.status.set("已凍結並保存目前畫面，可選手動四點／自動量測；想重拍請按『開始／回到預覽』。")
        except (OSError, ValueError) as error:
            self.status.set(f"已凍結，但原圖保存失敗：{error}")
            messagebox.showerror("存檔失敗", str(error))

    def stop_preview(self):
        if self.busy:
            return
        was_live = self.previewing
        self.previewing = False
        if self.stream:
            self.stream.close()
            self.stream = None
        self.visible_frame = None
        if was_live:
            self.set_image_empty()
        self.status.set("已停止串流。已拍下的照片仍可量測；尚未拍照的預覽不會保留。")

    def open_path(self, path):
        self.previewing = False
        super().open_path(path)

    def close(self):
        self.root.after_cancel(self.live_timer)
        if self.stream:
            self.stream.close()
        super().close()


def main():
    parser = argparse.ArgumentParser(description="Ameba Wi-Fi 即時預覽 → 拍照 → 腳長量測")
    parser.add_argument("--url", default="")
    parser.add_argument("--output", type=Path, default=Path("foot_captures"))
    args = parser.parse_args()
    root = tk.Tk()
    app = LiveFootApp(root, args.output, args.url)
    if args.url:
        root.after(300, app.start_preview)
    root.mainloop()


if __name__ == "__main__":
    main()
