"""Ameba Mini 語音控制 LED 系統的電腦端主程式。"""

from __future__ import annotations

import argparse

from command import Command, parse_command
from serial_controller import AmebaController, CommunicationError, MockAmebaController, SerialAmebaController
from speech import SpeechRecognitionError, recognize_from_microphone


def print_status(status: dict[str, bool], simulated: bool) -> None:
    """清楚區分模擬狀態與開發板實際回傳的狀態。"""
    source = "模擬 Ameba 回覆（非實體 LED 驗證）" if simulated else "Ameba 開發板實際回覆"
    blue = "亮" if status["blue"] else "滅"
    green = "亮" if status["green"] else "滅"
    print(f"{source}：藍燈={blue}，綠燈={green}")


def process_text(text: str, controller: AmebaController, debug: bool = False) -> None:
    """顯示辨識文字、白名單判斷結果與執行回饋。"""
    command = parse_command(text)
    print(f"辨識結果：{text}")
    if command is Command.UNKNOWN:
        print("判定：非控制指令；不傳送任何資料，LED 狀態不變。")
        if debug:
            code_points = " ".join(f"U+{ord(character):04X}" for character in text)
            print(f"除錯：語音文字 repr={text!r}")
            print(f"除錯：Unicode={code_points}")
        return
    print(f"判定：{command.name}；準備傳送：{command.protocol_message.strip()}")
    try:
        status = controller.send(command)
    except CommunicationError as error:
        print(f"通訊失敗：{error}。指令未確認執行，LED 實際狀態未知。")
        return
    print("指令已獲確認。")
    print_status(status, controller.is_simulated)


def get_input(use_microphone: bool, language: str) -> str:
    if use_microphone:
        try:
            return recognize_from_microphone(language=language)
        except SpeechRecognitionError as error:
            print(f"語音辨識失敗：{error}")
            return ""
    return input("\n請輸入模擬語音（輸入 exit 結束）：").strip()


def build_controller(args: argparse.Namespace) -> AmebaController:
    if args.mode == "mock":
        return MockAmebaController(disconnected=args.simulate_disconnect)
    if not args.port:
        raise ValueError("serial 模式必須指定 --port，例如 --port COM3")
    return SerialAmebaController(port=args.port, baudrate=args.baudrate)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ameba Mini 語音控制 LED")
    parser.add_argument("--mode", choices=("mock", "serial"), default="mock")
    parser.add_argument("--port", help="Ameba 的序列埠，例如 COM3")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--mic", action="store_true", help="從麥克風辨識繁體中文語音")
    parser.add_argument(
        "--language",
        choices=("zh-TW", "en-US"),
        default="zh-TW",
        help="麥克風辨識語言；英文指令使用 en-US",
    )
    parser.add_argument("--simulate-disconnect", action="store_true", help="模擬通訊中斷")
    parser.add_argument("--debug", action="store_true", help="顯示無法辨識指令的 Unicode 除錯資訊")
    args = parser.parse_args()
    try:
        controller = build_controller(args)
    except ValueError as error:
        parser.error(str(error))
        return
    except CommunicationError as error:
        print(f"通訊失敗：{error}")
        print("請關閉 Arduino Serial Monitor 或其他正在使用該 COM 埠的程式後再試。")
        return
    print("Ameba Mini LED 控制程式")
    print("模式：" + ("模擬" if controller.is_simulated else f"序列埠 {args.port}"))
    print("合法指令：左邊／右邊開燈、關燈、閃爍三次；亦支援英文指令。")
    try:
        while True:
            text = get_input(args.mic, args.language)
            if not text:
                continue
            if text.lower() in {"exit", "quit", "離開"}:
                print("程式結束。")
                break
            process_text(text, controller, debug=args.debug)
    except (KeyboardInterrupt, EOFError):
        print("\n程式結束。")
    finally:
        controller.close()


if __name__ == "__main__":
    main()
