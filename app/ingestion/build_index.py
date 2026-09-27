# CLI: walks data/<category>/*, chunks, embeds, and persists to the Chroma collection
# with `category` metadata set from the parent folder name. Ingestion phase.

from app.ingestion.chunking import chunk_documents
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.core.config import get_settings

settings = get_settings()

model_name = settings.embedding_model
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}

hf = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
)

if __name__ == "__main__":
    chunks = chunk_documents()
    ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    vectorstore = Chroma.from_documents(
        documents=chunks,
        ids=ids,
        embedding=hf,
        persist_directory=settings.chroma_persist_dir,
        collection_name="finsolve_docs",
    )
    print(f"Indexed {len(chunks)} chunks into {settings.chroma_persist_dir}")
