### Talk and Role Backend

# 초기세팅
1. pyenv install 3.13.1

2. pyenv local 3.13.1

3. python -m venv venv

4. venv\Scripts\activate(윈도우) / source venv/bin/activate(리눅스)

5. pip3 install <설치 해야 하는 것>
Ex) pip3 install alembic / pip install alembic(pip3가 안 될 때)
  -설치 해야하는 것
  1. alembic
  2. azure-cognitiveservices-speech
  3. fastapi
  4. openai
  5. uvicorn
  6. pydantic
  7. python-multipart

6. 서버 실행 코드
  1. source venv/bin/activate -> 가상 머신 접속
  2. uvicorn app:app --host 0.0.0.0 --port 8000

FastAPI Swagger 여는법
  1. http://localhost:8000/docs
