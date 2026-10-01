"""電腦端麥克風語音辨識。"""

from __future__ import annotations


class SpeechRecognitionError(RuntimeError):
    """麥克風、網路或語音辨識服務的錯誤。"""


def recognize_from_microphone(language: str = "zh-TW") -> str:
    """錄一段語音並回傳辨識文字。

    此範例使用 Google Web Speech，因此需要網路。辨識失敗時不產生 LED 指令。
    """
    try:
        import speech_recognition as sr
    except ImportError as error:
        raise SpeechRecognitionError("缺少 SpeechRecognition/PyAudio 套件") from error
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("請說話（例如：左邊開燈）…")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
        return recognizer.recognize_google(audio, language=language)
    except sr.WaitTimeoutError as error:
        raise SpeechRecognitionError("等待語音逾時") from error
    except sr.UnknownValueError as error:
        raise SpeechRecognitionError("無法辨識這段語音；LED 未改變") from error
    except sr.RequestError as error:
        raise SpeechRecognitionError(f"語音服務連線失敗：{error}") from error
    except OSError as error:
        raise SpeechRecognitionError(f"無法使用麥克風：{error}") from error
