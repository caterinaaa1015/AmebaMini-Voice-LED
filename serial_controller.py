"""Ameba USB Serial 通訊，以及無硬體時使用的模擬控制器。"""

from __future__ import annotations

from abc import ABC, abstractmethod
import time

from command import Command


class CommunicationError(RuntimeError):
    """無法送達指令或未收到有效開發板回覆。"""


class AmebaController(ABC):
    is_simulated: bool = False

    @abstractmethod
    def send(self, command: Command) -> dict[str, bool]:
        """傳送指令並回傳由 Ameba 回覆解析出的 LED 狀態。"""

    def close(self) -> None:
        """讓兩種控制器有相同的清理介面。"""


class MockAmebaController(AmebaController):
    """供無開發板時測試流程；回覆絕不可當作實體 LED 證據。"""

    is_simulated = True

    def __init__(self, disconnected: bool = False) -> None:
        self.disconnected = disconnected
        self._status = {"blue": False, "green": False}

    def send(self, command: Command) -> dict[str, bool]:
        if self.disconnected:
            raise CommunicationError("模擬：USB Serial 已中斷")
        if command is Command.BLUE_ON:
            self._status["blue"] = True
        elif command is Command.BLUE_OFF:
            self._status["blue"] = False
        elif command is Command.GREEN_ON:
            self._status["green"] = True
        elif command is Command.GREEN_OFF:
            self._status["green"] = False
        elif command is Command.BLUE_BLINK_3:
            # A three-blink command deliberately ends with the target LED off.
            self._status["blue"] = False
        elif command is Command.GREEN_BLINK_3:
            self._status["green"] = False
        else:
            raise CommunicationError("拒絕傳送 UNKNOWN 指令")
        return self._status.copy()


class SerialAmebaController(AmebaController):
    """與日後 Ameba 韌體的單行文字協定通訊。"""

    RESPONSE_PREFIX = "STATUS,"

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 4.0) -> None:
        try:
            import serial  # pyserial 僅在真實序列埠模式時才需要
        except ImportError as error:
            raise CommunicationError("缺少 pyserial；請執行 pip install -r requirements.txt") from error
        try:
            self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            self._timeout = timeout
            # Arduino boards can print boot text when the serial port opens.
            # Do not mistake that text for the response to the first LED command.
            time.sleep(0.6)
            self._serial.reset_input_buffer()
        except serial.SerialException as error:
            raise CommunicationError(f"無法開啟 {port}: {error}") from error

    def send(self, command: Command) -> dict[str, bool]:
        if command is Command.UNKNOWN:
            raise CommunicationError("拒絕傳送 UNKNOWN 指令")
        try:
            self._serial.write(command.protocol_message.encode("utf-8"))
            self._serial.flush()
        except Exception as error:
            raise CommunicationError(f"序列埠讀寫失敗：{error}") from error

        deadline = time.monotonic() + self._timeout
        last_response = ""
        while time.monotonic() < deadline:
            try:
                response = self._serial.readline().decode("utf-8", errors="replace").strip()
            except Exception as error:
                raise CommunicationError(f"序列埠讀寫失敗：{error}") from error
            if not response:
                continue
            last_response = response
            if response.startswith(self.RESPONSE_PREFIX):
                return self._parse_status(response)
            if response.startswith("ERROR,"):
                raise CommunicationError(f"Ameba 回覆錯誤：{response}")
        raise CommunicationError(f"未收到有效狀態回覆：{last_response or '逾時'}")

    def _parse_status(self, response: str) -> dict[str, bool]:
        # Ameba 預期格式：STATUS,BLUE=ON,GREEN=OFF
        if not response.startswith(self.RESPONSE_PREFIX):
            raise CommunicationError(f"未收到有效狀態回覆：{response or '逾時'}")
        values = dict(item.split("=", 1) for item in response.split(",")[1:] if "=" in item)
        if values.get("BLUE") not in {"ON", "OFF"} or values.get("GREEN") not in {"ON", "OFF"}:
            raise CommunicationError(f"狀態格式不完整：{response}")
        return {"blue": values["BLUE"] == "ON", "green": values["GREEN"] == "ON"}

    def close(self) -> None:
        if hasattr(self, "_serial") and self._serial.is_open:
            self._serial.close()
