### Talk and Role Backend

# 초기세팅

pip3 install <설치 해야 하는 것>
Ex) pip3 install alembic / pip install alembic

설치 해야하는 것

1. alembic
2. azure-cognitiveservices-speech
3. fastapi
4. openai
5. uvicorn
6. pydantic

서버 실행 코드

1. source venv/bin/activate -> 가상 머신 접속
2. uvicorn app:app --host 0.0.0.0 --port 8000

FastAPI Swagger 여는법

1. http://localhost:8000/docs
