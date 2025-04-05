from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
from service.pronunciation_evaluation import PronunciationEvaluator
from service.speech_to_text import SpeechToTextConverter
from service.gpt_evaluation import GptEvaluation 


app = FastAPI()

# Azure Speech 서비스 서브스크립션 키와 서비스 리전 설정
subscription_key = "Notion 참고"
service_region = "Notion 참고"

# 발음 평가
evaluator = PronunciationEvaluator(subscription_key, service_region)
@app.post("/evaluate-pronunciation/")
async def evaluate_pronunciation(file: UploadFile = File(...)):
    file_location = f"./{file.filename}"
    
    # 파일 저장
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    # 발음 평가
    reference_text = ""  # 여기에 평가할 참조 텍스트 추가
    result = await evaluator.evaluate_pronunciation(file_location, reference_text)

    # 임시 파일 삭제
    os.remove(file_location)

    return result

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
async def evaluate_text(request: TextEvaluationRequest):
    try:
        # GptEvaluation을 사용하여 텍스트를 평가
        completion = gpt_evaluator.evaluate_text(request.text)
        return {
            "evaluation": completion
        }
    except Exception as e:
        # 오류 발생 시 적절한 HTTP 상태와 메시지 반환
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)