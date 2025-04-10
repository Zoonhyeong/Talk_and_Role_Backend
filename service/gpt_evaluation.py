import os
from openai import AzureOpenAI  

class GptEvaluation:
    def __init__(self):
        # Azure OpenAI 클라이언트 초기화
        self.endpoint = os.getenv("OPENAI_ENDPOINT_URL")
        self.deployment = os.getenv("DEPLOYMENT_NAME")
        self.subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

        self.client = AzureOpenAI(  
            azure_endpoint=self.endpoint,  
            api_key=self.subscription_key,  
            api_version="2024-05-01-preview",
        )

    def prepare_chat_prompt(self, user_input: str):
        """ 사용자 입력에 대한 평가 요청의 프롬프트를 준비합니다. """
        return [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "너는 그 문장을 단어 개수를 센 다음에 "
                            "틀린 단어의 개수가 전체 단어 개수의 0퍼센트이면 100점, "
                            "1~10퍼센트는 90점, 11~20퍼센트면 80점, "
                            "21~30퍼센트면 70점을 주는 선생님이야. "
                            "그 점수와 단어가 수정된 올바른 문장을 같이 말해줘야 해."
                            "그리고 대소문자 구분은 채점 기준에 넣지말고 평가해줘."
                            "마지막에 발음점수와 유창성점수도 결과값에 추가해서 같이 보여줘"
                        )
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_input
                    }
                ]
            }
        ]

    def evaluate_text(self, text: str):
        """ 입력된 텍스트를 평가합니다. """
        messages = self.prepare_chat_prompt(text)

        # GPT 모델 호출
        completion = self.client.chat.completions.create(  
            model=self.deployment,
            messages=messages,
            max_tokens=800,  
            temperature=0.7,  
            top_p=0.95,  
            frequency_penalty=0,  
            presence_penalty=0,
            stop=None,  
            stream=False
        )

        return completion