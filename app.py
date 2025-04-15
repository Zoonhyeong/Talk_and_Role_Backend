from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
from service.pronunciation_evaluation import PronunciationEvaluator
from service.speech_to_text import SpeechToTextConverter
from service.gpt_evaluation import GptEvaluation
from service.text_to_speech import TextToSpeechConverter
from dotenv import load_dotenv
from openai import AzureOpenAI
from prompt import system_prompt

import json

app = FastAPI()
load_dotenv()

subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
service_region = os.getenv("AZURE_SERVICE_REGION")
tts_subscription_key = os.getenv("AZURE_TTS_SUBSCRIPTION_KEY")

history = []
sys_prompt = system_prompt

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
sst_converter = SpeechToTextConverter(subscription_key, service_region)

@app.post("/convert-speech-to-text/")
async def convert_speech_to_text(file: UploadFile = File(...)):
    file_location = f"./{file.filename}"
    
    # 파일 저장
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    # 음성 인식 수행
    transcription = await sst_converter.convert_speech_to_text(file_location)

    # 임시 파일 삭제
    os.remove(file_location)

    return {"transcription": transcription}

class TextEvaluationRequest(BaseModel):
    text: str

# TTS 변환
tts_converter = TextToSpeechConverter(tts_subscription_key, service_region)

@app.post("/convert-text-to-speech/")
async def convert_text_to_speech(input_text: str):
    output_file_path = "./output_speech.wav"  # 출력 파일 경로 설정

    # 텍스트 음성 변환 수행
    result = tts_converter.convert_text_to_speech(input_text, output_file_path)

    return result

# GPT -> 문법 평가
gpt_evaluator = GptEvaluation()

@app.post("/evaluate-text/")
async def evaluate_text(request: TextEvaluationRequest, pronunciation_score: str = None, fluency_score: str = None):
    try:
        # 발음 평가 결과가 있을 경우 이를 사용
        pronunciation_score_info = f"발음 평가 점수: {pronunciation_score or 'N/A'}, 유창성 점수: {fluency_score or 'N/A'}"

        evaluation_text = f"{request.text} {pronunciation_score_info}"
        completion = gpt_evaluator.evaluate_text(evaluation_text)

        next_npc_conversation = ""
        _next = json.loads(completion.choices[0].message.content)
        if "main_response" in _next:
            if "conversation" in _next.get("main_response"):
                # print("next_npc_ :", _next["main_response"]["conversation"][-1]["npc"])
                next_npc_conversation = _next["main_response"]["conversation"][-1]["npc"]
                
        print("next_conv:",next_npc_conversation)
        return {
            "evaluation": completion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-evaluate-text/")
async def test_evaluate_text(request: TextEvaluationRequest, pronunciation_score: str = None, fluency_score: str = None):
    try:
        # 발음 평가 결과가 있을 경우 이를 사용
        pronunciation_score = pronunciation_score  # 예시 값
        fluency_score = fluency_score 

        global history

        # print(system_prompt)
        # print(user_history)
        # print(assistant_histroy)
        # evaluation_text = f"{request.text} {pronunciation_score_info}"
        print("req:",request.text)
        if request.text[:1] == "{":
            history = []
            history.append(sys_prompt)

        history.append({"role":"user", "content":[{"type":"text","text":request.text}]})
        evaluation_text = history
        # print(evaluation_text)
        completion = gpt_evaluator.test_evaluate_text(evaluation_text)
        next_npc_conversation = ""

        history.append({"role":"assistant", "content":[{"type":"text","text":completion.to_json()}]})
        _next = json.loads(completion.choices[0].message.content)

        # print(_next)
        print(type(_next))
        if "main_response" in _next:
            if "conversation" in _next.get("main_response"):
                print("next_npc_ :", _next["main_response"]["conversation"][-1]["npc"])
                next_npc_conversation = _next["main_response"]["conversation"][-1]["npc"]
                tts_file_name = await convert_text_to_speech(next_npc_conversation)
                if pronunciation_score != None:
                    conversation_entry = _next["main_response"]["conversation"][-2]
                    conversation_entry["pronunciation_score"] = pronunciation_score
                    conversation_entry["fluency_score"] = fluency_score

        completion.choices[0].message.content = json.dumps(_next, ensure_ascii=False)

        return {
            "evaluation": completion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)