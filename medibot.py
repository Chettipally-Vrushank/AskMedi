import os
import streamlit as st

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


# -------------------- Config --------------------
DB_FAISS_PATH = "vectorstore/db_faiss"
HF_TOKEN = os.getenv("HF_TOKEN")

# Choose a chat-capable HF model that your account can access
# You can also try variants like ":fastest" depending on your HF router setup.
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"


st.set_page_config(
    page_title="AskMedi",
    page_icon="🩺",
    layout="wide",
)


# -------------------- Backend: Vector store & QA chain --------------------
@st.cache_resource
def get_vectorstore():
    """Load FAISS vectorstore once per session."""
    if not os.path.exists(DB_FAISS_PATH):
        raise FileNotFoundError(
            f"FAISS index not found at {DB_FAISS_PATH}. "
            f"Make sure you've created it before running the app."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    db = FAISS.load_local(
        DB_FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return db


def format_docs(docs):
    """Convert retrieved docs into a single context string."""
    parts = []
    for i, d in enumerate(docs, start=1):
        parts.append(f"[Document {i}]\n{d.page_content}")
    return "\n\n".join(parts)


@st.cache_resource
def get_qa_chain():
    """Build and cache the RAG chain (retriever + chat model)."""
    if HF_TOKEN is None:
        raise ValueError(
            "HF_TOKEN environment variable is not set. "
            "Please set HF_TOKEN to your Hugging Face API token."
        )

    db = get_vectorstore()
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # Chat prompt template
    base_template = """
Use only the information provided in the context to answer the user's question.
If you don't know the answer from the context, say "I don't know" and do not try to make up an answer.
Do not use any outside knowledge beyond the given context.

Context:
{context}

Question:
{question}

Start the answer directly. No small talk.
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are AskMedi, an assistant that answers medical questions "
                "strictly based on the given context. You are NOT a doctor and "
                "do not provide diagnoses or treatment prescriptions.",
            ),
            ("human", base_template),
        ]
    )

    # Chat model via HF router (OpenAI-compatible)
    chat_model = ChatOpenAI(
        model=MODEL_ID,
        api_key=HF_TOKEN,                          # Hugging Face token
        base_url="https://router.huggingface.co/v1",
        temperature=0.3,
        max_tokens=512,
    )

    # Base RAG chain
    base_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | chat_model
    )

    # Return both answer and source documents
    qa_chain = RunnableParallel(
        result=base_chain,
        source_documents=retriever,
    )

    return qa_chain


# -------------------- Frontend: Streamlit UI --------------------
def main():
    st.title("🩺 AskMedi")
    st.caption(
        "Ask questions based on your uploaded medical knowledge base. "
        "Answers are generated from your documents and are **not** a substitute for professional medical advice."
    )

    # Sidebar: info + controls
    with st.sidebar:
        st.header("About AskMedi")
        st.markdown(
            """
This assistant:

- Uses your FAISS knowledge base
- Answers *only* from the stored context
- Will say **\"I don't know\"** if the context is insufficient

> ⚠️ **Disclaimer:**  
> This tool is for informational and educational purposes only  
> and does **not** provide medical diagnosis or treatment.
            """
        )

        if st.button("🧹 Clear chat history"):
            st.session_state["messages"] = []
            st.success("Chat history cleared.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Render existing messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input box
    prompt = st.chat_input("Ask a medical-related question based on your knowledge base...")
    if prompt:
        # Show user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get QA chain
        qa_chain = get_qa_chain()

        # LLM response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = qa_chain.invoke(prompt)

                # result["result"] is an AIMessage when using ChatOpenAI
                answer_msg = result["result"]
                answer_text = (
                    answer_msg.content
                    if hasattr(answer_msg, "content")
                    else str(answer_msg)
                )

                st.markdown(answer_text)

                # Optional: show sources
                with st.expander("🔍 View retrieved source documents"):
                    for i, doc in enumerate(result["source_documents"], start=1):
                        st.markdown(f"**Source {i}**")
                        meta_lines = [
                            f"- `{k}`: {v}"
                            for k, v in doc.metadata.items()
                        ]
                        if meta_lines:
                            st.markdown("**Metadata:**")
                            st.markdown("\n".join(meta_lines))
                        st.markdown("**Excerpt:**")
                        st.markdown(doc.page_content[:800] + "...")
                        st.markdown("---")

        # Save assistant message to history
        st.session_state["messages"].append(
            {"role": "assistant", "content": answer_text}
        )


if __name__ == "__main__":
    main()
