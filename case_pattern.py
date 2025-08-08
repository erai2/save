# pdf_case_pattern_ai_init.py

import os, sqlite3, re, pandas as pd
from tqdm import tqdm
from langchain.document_loaders import PyPDFLoader
from langchain.llms import OpenAI

PDF_PATH = "Part_18._교육자.pdf"

# [1] DB 초기화/예시 패턴 자동 추가
def init_db(db_path="mng_db.sqlite3"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern TEXT, gekuk TEXT, explain TEXT
    )''')
    # 예시 패턴 추가 (필요시 직접 수정/추가)
    example_patterns = [
        (r"갑일주", "목격국", "갑일주는 목의 기운이 강하다."),
        (r"병화", "화격국", "병화는 태양과 같다.")
    ]
    # 이미 등록된 패턴이 없을 때만 추가
    c.execute("SELECT COUNT(*) FROM patterns")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO patterns (pattern, gekuk, explain) VALUES (?, ?, ?)", example_patterns)
    conn.commit()
    conn.close()

# [2] 패턴DB 분석 함수
def db_gekuk_analyze(text, db_path="mng_db.sqlite3"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT pattern, gekuk, explain FROM patterns")
    for patt, gekuk, explain in c.fetchall():
        try:
            if re.search(patt, text):
                conn.close()
                return gekuk, explain, patt
        except Exception:
            continue
    conn.close()
    return None, None, None

# [3] PDF에서 사례 불러오기
PDF_PATH = "Part_18._교육자.pdf"   # 분석할 PDF 파일명/경로 입력
loader = PyPDFLoader(PDF_PATH)
docs = loader.load_and_split()
print(f"PDF에서 {len(docs)}건 사례 추출")

# [4] OpenAI LLM
os.environ["OPENAI_API_KEY"] = "sk-"  # 본인키 입력!
llm = OpenAI(temperature=0.1)

# [5] DB 생성/초기화 (최초 실행시)
init_db("mng_db.sqlite3")

# [6] 사례별 분석 및 결과 저장
results = []
for doc in tqdm(docs, desc="분석중"):
    text = doc.page_content.strip()
    if not text:
        continue
    gekuk, explain, patt = db_gekuk_analyze(text)
    if gekuk:
        ai_text = f"[패턴DB] {gekuk} | {explain}"
    else:
        prompt = f"""아래 명리 사례(또는 문장)의 격국 및 규칙, 간단한 해설을 생성해줘.
가능하다면 격국명, 핵심 규칙/패턴, 간단한 해설을 각각 1줄씩 출력:
사례: {text}
"""
        ai_text = llm(prompt)
        patt = ""
    results.append({
        "원문": text,
        "패턴격국": gekuk or "",
        "패턴설명": explain or "",
        "적중패턴": patt or "",
        "AI해설": ai_text.strip()
    })

# [7] 결과 파일로 저장
out_csv = "분석결과.csv"
pd.DataFrame(results).to_csv(out_csv, index=False, encoding="utf-8-sig")
print(f"\n총 {len(results)}건 분석 완료! → {out_csv} 파일로 저장됨.")
