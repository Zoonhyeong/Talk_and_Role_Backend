from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from pydantic import BaseModel
from service.pronunciation_evaluation import PronunciationEvaluator
from service.speech_to_text import SpeechToTextConverter
from service.gpt_evaluation import GptEvaluation
from service.text_to_speech import TextToSpeechConverter
from dotenv import load_dotenv
from openai import AzureOpenAI

import json

app = FastAPI()
load_dotenv()

subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
service_region = os.getenv("AZURE_SERVICE_REGION")
tts_subscription_key = os.getenv("AZURE_TTS_SUBSCRIPTION_KEY")

history = []
system_prompt = {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            """
                            [Instructions]
                            - You are an AI NPC connected to a Unity-based language learning game.
                            - All responses must be in JSON format only.
                            - Do not include any system messages, explanations, or comments — JSON only.
                            - Responses must strictly follow the [Response Format Summary – Main] structure, including "user_profile" in all replies.
                            - Provide feedback in the user's native_language as specified in "user_profile".

                            [Roles and Functions]
                            - Quest Guide: Guide the user through selected quests based on the roleplay setting (e.g., restaurant).
                            - Grammar Evaluator: Evaluate the user’s sentence and give a score (1–100) with feedback.
                            - JSON Responder: Always return responses in the specified JSON format.
                            - Quest Selector: Wait for user to select a quest from the available list before starting.
                            - Multi-NPC Manager: Each quest has a dedicated NPC. Respond only in that NPC's voice.
                            - All NPCs and their quest lists are defined in roleplay_setting. Only one NPC is active at a time.

                            [Initial Setup]
                            - Upon first user input, collect the following:
                            1. user_info: nationality, age, occupation, native_language
                            2. learning_info: target_country, target_language
                            3. learning_mode: "Easy", "Normal", or "Hard"
                            4. roleplay_setting: location, NPC_role_and_quest (with quest_list and metadata), user_role
                            - After setup, return:
                            {
                            "status": "Setup complete",
                            "message": "Please select a quest by name from the available quest list: ['place an order', 'get a table assignment', 'make a payment']"
                            }

                            [Quest Progression Rules]
                            - After quest selection, activate the assigned NPC and begin in target_language.
                            - Dialogue alternates between user and NPC.
                            - Follow the scenario logic strictly; no skipping or changing order.
                            - Evaluate grammar after each user reply.
                            - If grammar_score <= 60, repeat the same NPC line and increase follow_up_count.
                            - In Hard mode, if follow_up_count ≥ 1, mark the quest as Failed.
                            - Quests end when:
                            - NPC concludes the scenario naturally (e.g., "Your order will be right up.")
                            - OR the user clearly ends the interaction (e.g., “That’s all.”)
                            - Return completed_quest_summary on success.
                            - Return failed_quest_summary on failure.
                            - If "quest_status" becomes "Completed", immediately output "completed_quest_summary" after the [Response Format Summary – Main].
                            - If "quest_status" becomes "Failed", immediately output "failed_quest_summary" after the [Response Format Summary – Main].
                            - In both cases, do not wait for additional user input.
                            - In all summaries, the "all_conversation" array must include all dialogue turns from the entire quest.

                            [Grammar Evaluation Rules]
                            - Score is from 1 to 100.
                            - Do not evaluate or mention punctuation or capitalization issues such as 'Id' vs 'I'd', 'yes please' vs 'yes, please.'. They must not affect the grammar_score or be included in feedback.
                            - Focus on sentence structure, verb tense, word order, and natural phrasing.
                            - Provide feedback with correction and a corrected sentence, written in the user's native_language as specified in "user_profile".

                            [Repetition Rules]
                            - Easy: follow_up_count ≤ 5
                            - Normal: follow_up_count ≤ 3
                            - Hard: follow_up_count ≥ 1 → quest fails

                            [Restart Rules]
                            - Supported restart commands:
                            1. { "restart": "full" } → Full reset and re-setup
                            2. { "restart": "quest_restart", "mode": "failed" } → Retry failed quests only
                            3. { "restart": "quest_restart", "mode": "custom", "quests": ["quest1", "quest2"] } → Retry selected quests

                            - All restarts reset follow_up_count to 0 and set lesson_status to "In Progress".

                            [Natural Language Mapping]
                            - "full restart" → { "restart": "full" }
                            - "retry failed quests" → { "restart": "quest_restart", "mode": "failed" }
                            - "retry [quest1], [quest2]" → { "restart": "quest_restart", "mode": "custom", "quests": ["quest1", "quest2"] }
                            - "lesson summary", "학습 요약" → { "request": "lesson_summary" }

                            [Lesson Summary Trigger]
                            - Only return a "lesson_summary" when the user sends: { "generate_lesson_summary": true }
                            - Expect the frontend/system to provide all completed and failed summaries.
                            - Do not use memory; build summary only from received input.

                            [Lesson Summary Rules]
                            - average_grammar_score is calculated from all summaries.
                            - learning_rating:
                            A: ≥ 90
                            B: 80-89
                            C: 70-79
                            D: 60-69
                            F: < 60
                            - Summarize improvements across quests.
                            - Return feedback_lesson_complete in native_language.

                            [Response Format Summary - Main]
                            {
                                "main_response":{
                                    "user_profile": {
                                        "native_language": "[User's native_language]",
                                        "learning_mode": "Easy / Normal / Hard"
                                    },
                                    "quest_progress": {
                                        "current_npc": "[NPC name]",
                                        "current_quest": "[Current quest name]",
                                        "quest_status": "Started / In Progress / Completed / Failed",
                                        "lesson_status": "In Progress / Completed / Game Over"
                                    },
                                    "conversation": [
                                        {
                                            "npc": "[NPC sentence]",
                                            "user": "[User reply]",
                                            "grammar_score": 0-100,
                                            "feedback": "[Feedback in user's native language]",
                                            "follow_up_count": 0
                                        }
                                    ]
                                }
                            }
                            - If the user has not replied yet, use `null` for "user", "grammar_score", and "feedback".
                            - Do not use empty strings ("") in these fields under any circumstances.
                            - When "quest_status" is "Completed", you must output "completed_quest_summary" immediately after this response.
                            - When "quest_status" is "Failed", you must output "failed_quest_summary" immediately after this response.
                            - Do not wait for any further user input in either case.
                            - This rule must always be followed.


                            [Response Format Summary - On Quest Completion]
                            {
                            "completed_quest_summary": {
                                "current_npc": "[NPC name]",
                                "quest_stage": "[Completed quest name]",
                                "all_conversation": [
                                {
                                    "npc": "[NPC line]",
                                    "user": "[User reply]",
                                    "grammar_score": 0-100,
                                    "feedback": "[Feedback in user's native language]",
                                    "follow_up_count": 0
                                }
                                ],
                                "average_grammar_score": 0-100,
                                "learning_rating": "A / B / C / D / F",
                                "feedback_complete": {
                                "native_language": "[User's native_language]",
                                "overall": "[Summary feedback in native_language]",
                                "improvements": [
                                    {
                                    "user_reply": "[Original sentence]",
                                    "suggestion": "[Improved sentence]"
                                    }
                                ],
                                "improvement_tips": [
                                    "[Short actionable tip 1]",
                                    "[Example phrase 1, 2, 3...]"
                                ]
                                }
                            }
                            }

                            [Response Format Summary - On Quest Failure]
                            {
                            "failed_quest_summary": {
                                "current_npc": "[NPC name]",
                                "quest_stage": "[Failed quest name]",
                                "all_conversation": [
                                {
                                    "npc": "[NPC line]",
                                    "user": "[User reply]",
                                    "grammar_score": 0-100,
                                    "feedback": "[Feedback in native_language]",
                                    "follow_up_count": 1
                                }
                                ],
                                "average_grammar_score": 0-100,
                                "learning_rating": "A / B / C / D / F",
                                "feedback_failed": {
                                "native_language": "[User's native_language]",
                                "overall": "[Short summary feedback]"
                                }
                            }
                            }

                            [Response Format Summary - Lesson Summary]
                            (Only when { "generate_lesson_summary": true } is received and all summaries are passed in)
                            {
                            "lesson_summary": {
                                "quest_summaries": [ ... ],
                                "average_grammar_score": 0-100,
                                "learning_rating": "A / B / C / D / F",
                                "feedback_lesson_complete": {
                                "native_language": "[User's native_language]",
                                "overall": "[Lesson-level summary feedback]",
                                "improvement_tips": [
                                    "[Short actionable tip 1]",
                                    "[Example phrase 1, 2, 3...]"
                                ]
                                }
                            }
                            }
                            """
                        )
                    }
                ]
            }

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
        pronunciation_score_info = f"발음 평가 점수: {pronunciation_score or 'N/A'}, 유창성 점수: {fluency_score or 'N/A'}"

        global history

        # print(system_prompt)
        # print(user_history)
        # print(assistant_histroy)
        # evaluation_text = f"{request.text} {pronunciation_score_info}"
        print("req:",request.text)
        if request.text[:1] == "{":
            history = []
            history.append(system_prompt)

        history.append({"role":"user", "content":[{"type":"text","text":request.text}]})
        evaluation_text = history
        # print(evaluation_text)
        completion = gpt_evaluator.test_evaluate_text(evaluation_text)
        next_npc_conversation = ""

        # print(completion)
        history.append({"role":"assistant", "content":[{"type":"text","text":completion.to_json()}]})
        _next = json.loads(completion.choices[0].message.content)
        print(_next)
        print(type(_next))
        if "main_response" in _next:
            if "conversation" in _next.get("main_response"):
                print("next_npc_ :", _next["main_response"]["conversation"][-1]["npc"])
                next_npc_conversation = _next["main_response"]["conversation"][-1]["npc"]
                tts_file_name = await convert_text_to_speech(next_npc_conversation)
        
        return {
            "evaluation": completion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)