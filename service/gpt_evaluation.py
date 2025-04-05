import os
from openai import AzureOpenAI  

class GptEvaluation:
    def __init__(self):
        # Azure OpenAI 클라이언트 초기화
        self.endpoint = os.getenv("ENDPOINT_URL", "Notion 참고")
        self.deployment = os.getenv("DEPLOYMENT_NAME", "Notion 참고")
        self.subscription_key = os.getenv("AZURE_OPENAI_API_KEY", " Notion 참고")  # 올바른 API 키로 설정

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