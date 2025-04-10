# Talk and Role Backend

### 초기세팅

1. pyenv install 3.13.1

2. pyenv local 3.13.1

3. python -m venv venv

4. venv\Scripts\activate(윈도우) / source venv/bin/activate(리눅스)

5. 라이브러리 다운로드

   1. pip install -r requirements.txt 사용하는 방식

      - pip freeze > requirements.txt로 한 팀원의 가상 환경의 라이브러리 버전을 requirements.txt에 저장
      - pip install -r requirements.txt로 모든 팀원이 해당 버전으로 라이브러리 설치
        - 깃헙의 Talk-and-Role/Talk_and_Role_Backend에 requirements.txt 있음

   2. 직접 다운로드하는 방식
      - pip3 install <설치 해야 하는 것>
        - Ex) pip3 install alembic / pip install alembic(pip3가 안 될 때)
      - 설치 해야하는 것
        1. alembic
        2. azure-cognitiveservices-speech
        3. fastapi
        4. openai
        5. uvicorn
        6. pydantic
        7. python-multipart

6. 엔드포인트, api-key 설정

   1. .env 파일 만들어 엔드포인트, api-key 정보 입력

      - Ex)

        ```
        AZURE_SUBSCRIPTION_KEY = ""
        AZURE_SERVICE_REGION = ""

        OPENAI_ENDPOINT_URL = openai 엔트포인트
        DEPLOYMENT_NAME = openai 배포명
        AZURE_OPENAI_API_KEY = openai api-key값
        ```

   2. 깃헙에 .env 파일까지 push되지 않도록, .gitignore에 .env 작성
   3. subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")처럼 os.getenv()로 엔드포인트, api-key 정보 불러옴

7. 서버 실행 코드

   1. venv\Scripts\activate(윈도우) / source venv/bin/activate(리눅스) -> 가상 머신 접속
   2. uvicorn app:app --host 0.0.0.0 --port 8000

8. FastAPI Swagger 여는법 1. http://localhost:8000/docs
