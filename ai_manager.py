import os, sqlite3, re, json
from tkinter import Tk, filedialog, messagebox
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms import OpenAI
import pandas as pd
from tqdm import tqdm

try:
    from docx import Document
except ImportError:
    Document = None

# OpenAI API키 입력
os.environ["OPENAI_API_KEY"] = "sk-"

# DB 초기화/생성
def init_db(db_path="mng_db.sqlite3"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern TEXT, gekuk TEXT, explain TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT, gekuk TEXT, explain TEXT, ai_text TEXT
    )''')
    conn.commit()
    conn.close()

def add_case(text, gekuk, explain, ai_text, db_path="mng_db.sqlite3"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO cases (text, gekuk, explain, ai_text) VALUES (?, ?, ?, ?)",
              (text, gekuk, explain, ai_text))
    conn.commit()
    conn.close()

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

def extract_texts_from_file(path):
    ext = os.path.splitext(path)[1].lower()
    texts = []
    if ext == ".pdf":
        loader = PyPDFLoader(path)
        docs = loader.load_and_split()
        texts = [doc.page_content.strip() for doc in docs if doc.page_content.strip()]
    elif ext in [".txt", ".md"]:
        with open(path, encoding="utf-8") as f:
            texts = [line.strip() for line in f if line.strip()]
    elif ext == ".csv":
        df = pd.read_csv(path, encoding="utf-8")
        # 모든 문자열 컬럼 합치거나 특정 컬럼 지정
        for idx, row in df.iterrows():
            row_text = " ".join([str(v) for v in row if isinstance(v, str) and v.strip()])
            if row_text: texts.append(row_text)
    elif ext == ".json":
        with open(path, encoding="utf-8") as f:
            j = json.load(f)
            # 리스트/딕셔너리 모두 지원
            if isinstance(j, list):
                for item in j:
                    if isinstance(item, dict):
                        row_text = " ".join([str(v) for v in item.values() if isinstance(v, str) and v.strip()])
                        if row_text: texts.append(row_text)
                    elif isinstance(item, str) and item.strip():
                        texts.append(item.strip())
            elif isinstance(j, dict):
                for v in j.values():
                    if isinstance(v, str) and v.strip():
                        texts.append(v.strip())
    elif ext == ".docx":
        if Document is None:
            raise RuntimeError("python-docx 모듈 설치 필요: pip install python-docx")
        doc = Document(path)
        texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    else:
        raise ValueError("지원하지 않는 파일 형식: " + ext)
    return texts

def analyze_and_save(file_path, db_path="mng_db.sqlite3"):
    texts = extract_texts_from_file(file_path)
    llm = OpenAI(temperature=0.1)
    cnt = 0
    for text in tqdm(texts, desc="분석중"):
        gekuk, explain, patt = db_gekuk_analyze(text, db_path)
        if gekuk:
            ai_text = f"[패턴DB] {gekuk} | {explain}"
        else:
            prompt = f"""아래 명리 사례(또는 문장)의 격국 및 규칙, 간단한 해설을 생성해줘.
가능하다면 격국명, 핵심 규칙/패턴, 간단한 해설을 각각 1줄씩 출력:
사례: {text}
"""
            ai_text = llm(prompt)
            if isinstance(ai_text, list): ai_text = ai_text[0]
            gekuk, explain = "", ""
        add_case(text, gekuk or "", explain or "", ai_text.strip(), db_path)
        cnt += 1
    messagebox.showinfo("분석 완료", f"{cnt}건 DB에 저장!")

def open_and_run():
    path = filedialog.askopenfilename(title="문서 파일 선택", filetypes=[
        ("모든 지원 파일", "*.pdf;*.txt;*.csv;*.json;*.md;*.docx"),
        ("PDF", "*.pdf"), ("TXT", "*.txt"), ("CSV", "*.csv"), ("JSON", "*.json"),
        ("MD", "*.md"), ("Word", "*.docx")
    ])
    if not path: return
    try:
        analyze_and_save(path)
    except Exception as e:
        messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    init_db()
    root = Tk()
    root.title("문서 분석 및 DB 축적기")
    from tkinter import Button, Label
    Label(root, text="PDF, Word, CSV, TXT, MD, JSON 자동 분석/DB저장", font=("맑은고딕", 14)).pack(pady=16)
    Button(root, text="문서 불러오기/분석", width=28, height=2, command=open_and_run).pack(pady=12)
    Label(root, text="(분석 후 SQLite DB: mng_db.sqlite3/cases에 자동 저장)", font=("맑은고딕", 11)).pack(pady=10)
    root.mainloop()
