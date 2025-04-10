from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
from service.pronunciation_evaluation import PronunciationEvaluator
from service.speech_to_text import SpeechToTextConverter
from service.gpt_evaluation import GptEvaluation
from dotenv import load_dotenv
from openai import AzureOpenAI

app = FastAPI()
load_dotenv()

subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
service_region = os.getenv("AZURE_SERVICE_REGION")

# 발음 평가
evaluator = PronunciationEvaluator(subscription_key, service_region)

@app.post("/evaluate-pronunciation/")
async def evaluate_pronunciation(reference_text: str, file: UploadFile):
    file_location = f"./{file.filename}"
    
    # 파일 저장
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    # 발음 평가
    pronunciation_result = await evaluator.evaluate_pronunciation(file_location, reference_text)

    # 임시 파일 삭제
    os.remove(file_location)

    # 발음 평가 결과를 포함한 리턴 값
    return {
        "recognized": pronunciation_result.get('recognized'),
        "pronunciation_score": pronunciation_result.get('pronunciation_score', 'N/A'),
        "fluency_score": pronunciation_result.get('fluency_score', 'N/A'),
        "mispronunciation_words": pronunciation_result.get('mispronunciation_words', 'N/A'),
    }

# STT 변환
converter = SpeechToTextConverter(subscription_key, service_region)

@app.post("/convert-speech-to-text/")
async def convert_speech_to_text(file: UploadFile = File(...)):
    file_location = f"./{file.filename}"
    
    # 파일 저장
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    # 음성 인식 수행
    transcription = await converter.convert_speech_to_text(file_location)

    # 임시 파일 삭제
    os.remove(file_location)

    return {"transcription": transcription}

class TextEvaluationRequest(BaseModel):
    text: str

# GPT -> 문법 평가
gpt_evaluator = GptEvaluation()

@app.post("/evaluate-text/")
async def evaluate_text(request: TextEvaluationRequest, pronunciation_score: str = None, fluency_score: str = None):
    try:
        # 발음 평가 결과가 있을 경우 이를 사용
        pronunciation_score_info = f"발음 평가 점수: {pronunciation_score or 'N/A'}, 유창성 점수: {fluency_score or 'N/A'}"

        evaluation_text = f"{request.text} {pronunciation_score_info}"
        completion = gpt_evaluator.evaluate_text(evaluation_text)

        return {
            "evaluation": completion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)