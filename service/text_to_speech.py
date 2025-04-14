import azure.cognitiveservices.speech as speechsdk

class TextToSpeechConverter:
    def __init__(self, subscription_key: str, service_region: str, voice_name: str = "en-US-AndrewMultilingualNeural"):
        self.speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
        self.speech_config.speech_synthesis_voice_name = voice_name  # 음성 선택

    def convert_text_to_speech(self, text: str, output_file_path: str):
        # 음성 합성을 위한 AudioConfig 설정
        audio_config = speechsdk.audio.AudioConfig(filename=output_file_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)

        # 텍스트를 음성으로 변환
        print("Converting text to speech...")
        result = synthesizer.speak_text_async(text).get()

        # 결과 처리
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized to file [{}]".format(output_file_path))
            return {"status": "success", "file_path": output_file_path}
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return {"status": "failure", "reason": cancellation_details.reason}
        
        # 여자로 말하면 좀 느립니다.