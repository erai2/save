
import os
import json
import re
from pathlib import Path
import pdfplumber
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.docstore.document import Document

# 1. 문서 텍스트 추출
def extract_text(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf_obj:
            return "\n".join([page.extract_text() or "" for page in pdf_obj.pages])
    return Path(file_path).read_text(encoding="utf-8")

# 2. 구조화: 사례/규칙 블록 추출
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

# 3. 임베딩 및 벡터 저장
def embed_and_save(blocks, db_dir, db_type="Chroma", embed_type="HF"):
    docs = [Document(page_content=f"[{b['구분']}] {b['제목']}\n{b['내용']}", metadata={"title": b["제목"]}) for b in blocks]
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") if embed_type == "HF" else OpenAIEmbeddings()

    if db_type == "Chroma":
        db = Chroma.from_documents(docs, emb, persist_directory=db_dir)
        db.persist()
    elif db_type == "FAISS":
        db = FAISS.from_documents(docs, emb)
        FAISS.save_local(db, db_dir)
    return db_dir

# 4. 실행
if __name__ == "__main__":
    files = [
        "C:/Users/oo/Desktop/new4/Book5_new.md",
        "C:/Users/oo/Desktop/new4/Part4 수암명리의 분석방법.md"
    ]

    all_blocks = []
    print("📂 문서 로딩 중...")
    for file_path in files:
        raw_text = extract_text(file_path)
        parsed_blocks = parse_cases(raw_text)
        all_blocks.extend(parsed_blocks)

    print(f"🔍 총 {len(all_blocks)}개 블록 구조화 완료")
    with open("saju_structured_all.json", "w", encoding="utf-8") as f:
        json.dump(all_blocks, f, ensure_ascii=False, indent=2)

    print("💾 JSON 저장 완료: saju_structured_all.json")

    # 벡터 DB 저장
    db_output = embed_and_save(all_blocks, db_dir="saju_vector_db", db_type="Chroma", embed_type="HF")
    print(f"✅ 벡터 DB 저장 완료: {db_output}")
