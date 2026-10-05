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

def header_path(metadata: dict) -> str:
    # "Employee Handbook > Welcome & Introduction > Core Values"
    headers = [metadata[key] for _, key in headers_to_split_on if key in metadata]
    return " > ".join(headers)


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
                # Prepend the heading path: strip_headers moves headings into
                # metadata, where neither the embedding nor BM25 can see them.
                path = header_path(split.metadata)
                if path:
                    split.page_content = f"{path}\n{split.page_content}"

            all_chunks.extend(splits)

        else:
            doc.metadata["chunk_id"] = f"hr-{doc.metadata["employee_id"]}"
            all_chunks.append(doc)

    return all_chunks
        