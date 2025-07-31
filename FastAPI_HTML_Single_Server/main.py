from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 정적 파일(HTML, CSS, JS) 서빙
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 질문 응답 API
@app.post("/query")
async def query(req: Request):
    data = await req.json()
    question = data.get("question", "")
    return {"answer": f"💬 질문 받음: {question}"}
