import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI


# 1. Set up Chat model (via HF router, OpenAI-compatible API)
HF_TOKEN = os.getenv("HF_TOKEN")

# Any chat-capable HF model that your account can use.
# You can also try variants like ":fastest" or ":novita", e.g.:
# MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct:fastest"
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"


def load_chat_model():
    if HF_TOKEN is None:
        raise ValueError(
            "HF_TOKEN environment variable is not set. "
            "Please set HF_TOKEN to your Hugging Face API token."
        )

    llm = ChatOpenAI(
        model=MODEL_ID,
        api_key=HF_TOKEN,                       # Hugging Face token
        base_url="https://router.huggingface.co/v1",  # HF router (chat-completions)
        temperature=0.5,
        max_tokens=512,
    )
    return llm


# 2. Custom prompt (as chat prompt)
custom_prompt_template = """
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
            "You are a strict QA assistant. You only answer using the given context. "
            "If the context is not enough, say you don't know.",
        ),
        (
            "human",
            custom_prompt_template,
        ),
    ]
)


# 3. Load FAISS vector store
DB_FAISS_PATH = "vectorstore/db_faiss"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = FAISS.load_local(
    DB_FAISS_PATH,
    embeddings,
    allow_dangerous_deserialization=True,
)

retriever = db.as_retriever(search_kwargs={"k": 3})


def format_docs(docs):
    """Convert retrieved docs into a single context string."""
    parts = []
    for i, d in enumerate(docs, start=1):
        parts.append(f"[Document {i}]\n{d.page_content}")
    return "\n\n".join(parts)


# 4. Build the RAG chain using Runnables
chat_model = load_chat_model()

# Base chain: takes a question, retrieves context, formats prompt, calls chat model
base_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | chat_model
)

# Wrap base_chain so that we also return the raw source documents
qa_chain = RunnableParallel(
    result=base_chain,
    source_documents=retriever,
)


if __name__ == "__main__":
    user_query = input("Enter Query here : ")

    # qa_chain takes the bare question string
    response = qa_chain.invoke(user_query)

    print("\n=== Result ===")
    # result is an AIMessage; print its content
    print(response["result"].content)

    print("\n=== Source Documents ===")
    for i, doc in enumerate(response["source_documents"], start=1):
        print(f"\n--- Document {i} ---")
        source = doc.metadata.get("source", "unknown")
        print(f"Source: {source}")
        print(doc.page_content[:500], "...")
