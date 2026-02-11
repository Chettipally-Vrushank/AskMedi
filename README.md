<div align="center">

# 🩺 AskMedi: AI-Powered Medical Chatbot
### _Your intelligent assistant for medical queries based on your knowledge base._

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32.0-red)
![LangChain](https://img.shields.io/badge/langchain-0.1.0-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Tech Stack](#tech-stack) • [Disclaimer](#disclaimer)

</div>

---

### 🌟 Overview

**AskMedi** is a RAG (Retrieval-Augmented Generation) application that allows users to ask medical questions and receive answers based *strictly* on a provided knowledge base (PDF documents). It uses a local FAISS vector store for retrieval and a Hugging Face LLM (via API) for generation, ensuring answers are grounded in the provided context.

### ✨ Features

*   **📚 RAG Architecture**: Retrieves relevant context from your own PDF documents before answering.
*   **🤖 Large Language Model**: Powered by `meta-llama/Llama-3.1-8B-Instruct` (via Hugging Face API).
*   **⚡ Fast Retrieval**: Uses FAISS (Facebook AI Similarity Search) for efficient vector similarity search.
*   **🖥️ User-Friendly Interface**: Built with Streamlit for an interactive chat experience.
*   **🔍 Source Citations**: Displays the specific document chunks used to generate each answer.
*   **🚫 Hallucination Control**: Strictly instructed to say "I don't know" if the answer isn't in the context.

---

### 🛠️ Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Chettipally-Vrushank/AskMedi.git
    cd AskMedi
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv env
    # Windows
    .\env\Scripts\activate
    # Mac/Linux
    source env/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    # OR if using Pipenv
    pipenv install
    ```

4.  **Configuration**
    Create a `.env` file in the root directory and add your Hugging Face API token:
    ```ini
    HF_TOKEN=your_hugging_face_api_token
    ```

---

### 🚀 Usage

#### 1. Prepare the Knowledge Base
Place your medical PDF documents in the `data/` directory.

#### 2. Create Vector Embeddings
Run the ingestion script to process PDFs and create the FAISS index:
```bash
python create_memory_for_llm.py
```
*This will create a `vectorstore/db_faiss` directory containing the vector index.*

#### 3. Run the Application
Launch the Streamlit app:
```bash
streamlit run medibot.py
```
Access the app in your browser at `http://localhost:8501`.

---

### 🏗️ Tech Stack

*   **Language**: Python
*   **Frontend**: Streamlit
*   **LLM Integration**: LangChain, Hugging Face Hub
*   **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
*   **Vector Store**: FAISS
*   **Model**: Meta Llama 3.1 8B Instruct

---

### ⚠️ Disclaimer

> **This tool is for informational and educational purposes only.**  
> It is **NOT** a substitute for professional medical advice, diagnosis, or treatment.  
> Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.