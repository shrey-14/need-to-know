# Metadata-filtered retriever: restricts search to categories from roles.allowed_categories(role). RAG phase.
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.core.config import get_settings
from app.core.roles import allowed_categories

settings = get_settings()

# Recorded in every eval run's manifest. Update when the retrieval approach
# changes (e.g. "hybrid-bm25-rrf", "hybrid-bm25-rrf+rerank").
RETRIEVAL_STRATEGY = "dense"

model_name = settings.embedding_model
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}

hf = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
)

vectorstore = Chroma(
    persist_directory=settings.chroma_persist_dir,
    collection_name="finsolve_docs",
    embedding_function=hf,
)

def get_relevant_documents(query: str, role: str, k: int = 5) -> list[Document]:
    categories = allowed_categories(role)
    if categories:
        results = vectorstore.similarity_search(
            query, k=k, filter={"category": {"$in": list(categories)}}
        )
        return results
    return []
    