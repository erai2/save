# app.py
# A self-contained web application for document analysis using Streamlit.
# This single file handles UI, server logic, and file operations.

import streamlit as st
import os
import time

# --- 1. Core Logic & Setup (Backend part) ---

# Directory to store uploaded files.
UPLOAD_DIRECTORY = "./uploaded_documents"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

def save_uploaded_file(uploaded_file):
    """Saves the uploaded file to the server's directory."""
    try:
        if uploaded_file is not None:
            file_path = os.path.join(UPLOAD_DIRECTORY, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return True
    except Exception as e:
        st.error(f"파일 저장 중 오류 발생: {e}")
        return False
    return False

def get_file_list():
    """Retrieves the list of saved files, sorted alphabetically."""
    return sorted(os.listdir(UPLOAD_DIRECTORY))

def delete_file(filename):
    """Deletes the specified file from the directory."""
    try:
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        st.error(f"파일 삭제 중 오류 발생: {e}")
    return False

def get_answer_from_ai(question, context_files):
    """
    (Core AI Function) Generates an answer based on the question and context files.
    In a real application, this function would integrate with libraries like
    LangChain, LlamaIndex, or directly call an AI model API (e.g., GPT).
    """
    if not question.strip():
        return "질문을 입력해주세요."
    if not context_files:
        return "답변의 근거가 될 문서를 먼저 업로드해주세요."

    # --- Placeholder for actual AI logic ---
    # 1. Read content from files in `context_files`.
    # 2. Create a prompt for the AI model, including the context and question.
    # 3. Call the AI model's API.
    # 4. Return the generated answer.
    # For this example, we'll simulate a delay and return a mock response.
    with st.spinner("AI가 문서를 분석하고 답변을 생성하는 중입니다..."):
        time.sleep(2) # Simulate AI thinking time
        mock_answer = (
            f"질문: '{question}'\n\n"
            f"답변: 이 답변은 '{', '.join(context_files)}' 파일(들)의 내용을 기반으로 생성된 예시입니다. "
            "실제 시스템에서는 이 부분에 AI 모델이 연동되어 심층적인 분석 결과를 제공합니다."
        )
    return mock_answer
    # --- End of placeholder ---


# --- 2. UI Rendering (Frontend part using Streamlit) ---

# Set page configuration (title, icon, layout)
st.set_page_config(
    page_title="통합 문서 분석 시스템",
    page_icon="🤖",
    layout="centered"
)

# Main title of the application
st.title("🤖 통합 문서 분석 시스템")
st.caption("Python과 Streamlit만으로 구현된 UI 및 서버 통합 애플리케이션")

# --- Section 1: File Upload ---
with st.container(border=True):
    st.header("1. 문서 업로드")
    # File uploader widget
    uploaded_file = st.file_uploader(
        "분석할 문서를 여기에 업로드하세요.",
        type=['pdf', 'txt', 'md', 'docx'],
        label_visibility="collapsed"
    )

    if uploaded_file:
        if save_uploaded_file(uploaded_file):
            st.success(f"✅ **{uploaded_file.name}** 파일이 성공적으로 업로드되었습니다!")
            # Rerun the script to immediately reflect the change in the file list
            st.rerun()

# --- Section 2: File Management ---
with st.container(border=True):
    st.header("2. 업로드된 문서 관리")
    file_list = get_file_list()

    if not file_list:
        st.info("현재 업로드된 문서가 없습니다. 위에서 문서를 추가해주세요.")
    else:
        # Display each file with a delete button
        for filename in file_list:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.markdown(f"📄 **{filename}**")
            with col2:
                # Use a unique key for each button to ensure they work independently
                if st.button("삭제", key=f"delete_{filename}"):
                    if delete_file(filename):
                        st.toast(f"🗑️ '{filename}' 파일이 삭제되었습니다.")
                        st.rerun()

# --- Section 3: Question & Answer ---
with st.container(border=True):
    st.header("3. AI에게 질문하기")
    # Text input for the user's question
    question = st.text_input(
        "업로드된 문서 내용에 대해 질문을 입력하세요:",
        placeholder="예: 문서의 핵심 주제는 무엇인가요?"
    )

    # Submit button
    if st.button("답변 생성", type="primary", use_container_width=True):
        answer = get_answer_from_ai(question, get_file_list())
        st.info(answer)