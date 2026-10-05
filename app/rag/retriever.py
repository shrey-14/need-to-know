# Metadata-filtered retriever: restricts search to categories from roles.allowed_categories(role). RAG phase.
import re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.core.config import get_settings
from app.core.roles import allowed_categories
from langchain_community.retrievers import BM25Retriever
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

settings = get_settings()

# Recorded in every eval run's manifest. Update when the retrieval approach
# changes (e.g. "hybrid-bm25-rrf", "hybrid-bm25-rrf+rerank").
RETRIEVAL_STRATEGY = "hybrid-bm25-rrf"

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

def tokenize(text: str) -> list[str]:
    lowercase_text = text.lower()
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", lowercase_text)
    tokens = [token for token in tokens if token not in ENGLISH_STOP_WORDS]
    return tokens

data = vectorstore.get(include=["documents", "metadatas"])

all_docs = [Document(page_content=t, metadata=m, id=i) for i, t, m in zip(data["ids"], data["documents"], data["metadatas"])]
bm25 = BM25Retriever.from_documents(all_docs, preprocess_func=tokenize, k=len(all_docs))

def rrf(result_lists: list[list[Document]], k: int, c: int = 60) -> list[Document]:
    # Reciprocal Rank Fusion (RRF) implementation
    scores, docs = {}, {}
    for result_list in result_lists:
        for rank, doc in enumerate(result_list):
            scores[doc.id] = scores.get(doc.id, 0) + 1 / (c + rank + 1)
            docs[doc.id] = doc

    top_ids = sorted(scores, key=scores.get, reverse=True)[:k]
    return [docs[i] for i in top_ids]



def get_relevant_documents(query: str, role: str, k: int = 5) -> list[Document]:
    dense_results = []
    bm25_results = []
    categories = allowed_categories(role)
    if categories:
        dense_results = vectorstore.similarity_search(
            query, k=20, filter={"category": {"$in": list(categories)}}
        )
        
        bm25_results = [d for d in bm25.invoke(query) if d.metadata["category"] in categories][:20]

        return rrf([dense_results, bm25_results], k=k)
    return []
    