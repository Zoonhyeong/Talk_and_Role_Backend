import azure.cognitiveservices.speech as speechsdk

def pronunciation_assessment_from_audio_file(audio_file_path):
    # Azure Speech 서비스 서브스크립션 키와 서비스 리전 설정
    subscription_key = "acIvLB1r31O3xwJm7UKSXTT4ePH78v9keqS8rUkxNCeknLuEWREcJQQJ99BDACYeBjFXJ3w3AAAYACOGAuFz"
    service_region = "eastus"

    # Speech SDK에 사용할 SpeechConfig 설정
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)

    # 발음 평가 설정
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text="",
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True
    )

    # 파일 입력을 위한 AudioConfig 객체 생성
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # 발음 평가를 위한 설정 적용
    pronunciation_config.apply_to(recognizer)

    print("Evaluating pronunciation from audio file...")
    result = recognizer.recognize_once()

    # 결과 처리
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized: {result.text}")

        # 발음 평가 결과 출력
        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
        print(f"Pronunciation Score: {pronunciation_result.pronunciation_score}")
        print(f"Accuracy Score: {pronunciation_result.accuracy_score}")
        print(f"Fluency Score: {pronunciation_result.fluency_score}")
        print(f"Completeness Score: {pronunciation_result.completeness_score}")
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech Recognition canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")

if __name__ == "__main__":
    audio_file_path = "/Users/leejunhyeong/Desktop/Microsoft AI School/4a281850-0f74-11f0-9bf5-2f5567ceb996.wav"
    pronunciation_assessment_from_audio_file(audio_file_path)