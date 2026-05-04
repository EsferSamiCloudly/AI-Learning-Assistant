from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(
    text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 100,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)


def split_pages(
    pages: list[dict],
    chunk_size: int = 400,
    chunk_overlap: int = 100,
) -> list[dict]:
    """
    Input: [{"page_number": int, "content": str}]
    Output: [{"chunk_index": int, "page_number": int, "content": str}]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = []
    chunk_index = 0

    for page in pages:
        if not page["content"].strip():
            continue
        page_chunks = splitter.split_text(page["content"])
        for chunk_text in page_chunks:
            if chunk_text.strip():
                chunks.append({
                    "chunk_index": chunk_index,
                    "page_number": page["page_number"],
                    "content": chunk_text,
                })
                chunk_index += 1

    return chunks