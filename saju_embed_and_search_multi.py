
import os
import re
import json
import pdfplumber
import pandas as pd
from pathlib import Path
from langchain.vectorstores import Chroma, FAISS
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.docstore.document import Document

# 📄 문서 → 텍스트
def extract_text(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join([page.extract_text() or "" for page in pdf])
    return Path(file_path).read_text(encoding="utf-8")

# 📘 텍스트 → 구조화
def parse_cases(text):
    pattern = re.split(r"(?:◉|<사례\s*\d+>|#\s*사례\s*\d+|사례\s*\d+|예시\s*\d+|■)", text)
    blocks = []
    for block in pattern:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        summary = " / ".join([l for l in body.splitlines() if l.strip()][:5])
        category = "사례" if "사례" in title else "규칙" if "법칙" in title else "기타"
        blocks.append({"제목": title, "내용": body, "요약": summary, "구분": category})
    return blocks

# 💾 벡터 저장
def embed_and_save(blocks, db_dir, db_type, embed_type):
    docs = [Document(page_content=f"[{b['구분']}] {b['제목']}\n{b['내용']}", metadata={"title": b["제목"]}) for b in blocks]
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") if embed_type == "HF" else OpenAIEmbeddings()
    if db_type == "Chroma":
        db = Chroma.from_documents(docs, emb, persist_directory=db_dir)
        db.persist()
    elif db_type == "FAISS":
        db = FAISS.from_documents(docs, emb)
        FAISS.save_local(db, db_dir)
    return db

# 🔍 유사도 검색
def search_vector(db_dir, query, db_type, embed_type, k=3):
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") if embed_type == "HF" else OpenAIEmbeddings()
    db = Chroma(persist_directory=db_dir, embedding_function=emb) if db_type == "Chroma" else FAISS.load_local(db_dir, emb)
    return db.similarity_search(query, k=k)

# 🧠 GPT 요약 (옵션)
def gpt_summary(query, docs):
    import openai
    combined = "\n\n".join([doc.page_content[:1000] for doc in docs])
    prompt = f"""
사용자 질문: {query}
아래는 관련된 사주 사례입니다. 격국, 제압 방식, 현실 해석을 요약해 주세요:

{combined}
"""
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return res.choices[0].message.content.strip()

# ✅ 실행 예시
if __name__ == "__main__":
    files = ["case.json", "DB.pdf"]  # 여러 파일 지정
    all_blocks = []
    for file_path in files:
        print(f"📂 {file_path} 불러오는 중...")
        raw_text = extract_text(file_path)
        blocks = parse_cases(raw_text)
        all_blocks.extend(blocks)

    print(f"✅ 총 {len(all_blocks)}건 구조화됨")
    df = pd.DataFrame(all_blocks)
    df.to_csv("saju_structured_all.csv", index=False, encoding="utf-8-sig")

    db_dir = "saju_vector_db"
    db_type = "Chroma"
    embed_type = "HF"

    print("🧠 벡터 DB 생성 중...")
    embed_and_save(all_blocks, db_dir, db_type, embed_type)
    print(f"✅ 저장 완료: {db_dir}")

    query = "甲日주에서 식신이 재를 생하면?"
    print(f"🔍 검색: {query}")
    results = search_vector(db_dir, query, db_type, embed_type, k=3)

    result_data = []
    for i, r in enumerate(results):
        print(f"\n{i+1}. {r.metadata['title']}\n{r.page_content[:500]}...")
        result_data.append({
            "순번": i + 1,
            "제목": r.metadata["title"],
            "내용": r.page_content[:1000]
        })

    pd.DataFrame(result_data).to_csv("search_results.csv", index=False, encoding="utf-8-sig")
    print("📁 검색 결과 저장 완료: search_results.csv")

    use_gpt = True
    if use_gpt:
        print("\n🧠 GPT 요약 결과:")
        print(gpt_summary(query, results))
