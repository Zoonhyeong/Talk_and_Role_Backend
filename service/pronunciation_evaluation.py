import azure.cognitiveservices.speech as speechsdk
import os

class PronunciationEvaluator:
    def __init__(self, subscription_key: str, service_region: str):
        self.speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)

    async def evaluate_pronunciation(self, audio_file_path: str, reference_text: str):
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )

        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)
        pronunciation_config.apply_to(recognizer)

        result = recognizer.recognize_once()

        # 결과 처리
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
            
            mispronunciation_words = []

            # Words 리스트를 순회
            for word_info in pronunciation_result.words:
                # 잘못된 발음인지 여부 확인
                if word_info.error_type == "Mispronunciation":
                    mispronunciation_words.append(word_info.word)

            return {
                "recognized": result.text,
                "pronunciation_score": pronunciation_result.pronunciation_score,
                "fluency_score": pronunciation_result.fluency_score,
                "mispronunciation_words": mispronunciation_words,
            }
        elif result.reason == speechsdk.ResultReason.NoMatch:   
            return {"error": "No speech could be recognized."}
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return {"error": f"Speech Recognition canceled: {cancellation_details.reason}"}