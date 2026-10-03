# Chunking strategy per file type. Ingestion phase.
from pathlib import Path
from app.ingestion.loaders import load_documents
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]

chunk_size = 800
chunk_overlap = 150

def chunk_documents() -> list[Document]:

    all_documents = load_documents()
    all_chunks = []
    markdown_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=headers_to_split_on, strip_headers=True
                )
    text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size, chunk_overlap=chunk_overlap
                )
    for doc in all_documents:
        if doc.metadata["source"].endswith(".md"):
            
            md_header_splits = markdown_splitter.split_text(doc.page_content)

            for split in md_header_splits:
                split.metadata.update(doc.metadata)

            # Split
            splits = text_splitter.split_documents(md_header_splits)

            source_name = Path(doc.metadata["source"]).stem
            for i, split in enumerate(splits):
                split.metadata["chunk_id"] = f"{source_name}-{i}"

            all_chunks.extend(splits)

        else:
            doc.metadata["chunk_id"] = f"hr-{doc.metadata["employee_id"]}"
            all_chunks.append(doc)

    return all_chunks
        