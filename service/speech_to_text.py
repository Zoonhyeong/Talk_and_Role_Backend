import azure.cognitiveservices.speech as speechsdk
import os

class SpeechToTextConverter:
    def __init__(self, subscription_key: str, service_region: str):
        self.speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)

    async def convert_speech_to_text(self, audio_file_path: str):
        # AudioConfig 설정
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

        # 음성 인식 수행
        print("Converting speech to text...")
        result = recognizer.recognize_once()

        # 결과 처리
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "No speech could be recognized."
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return f"Speech Recognition canceled: {cancellation_details.reason}"