import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


class DocumentChunker:

    def __init__(self, project_dir: str):

        self.project_dir = Path(project_dir)

        self.markdown_file = (
            self.project_dir
            / "markdown"
            / f"{self.project_dir.name}.md"
        )

        self.output_dir = self.project_dir / "chunks"

        self.output_dir.mkdir(parents=True, exist_ok=True)



    @staticmethod
    def _is_special(text):

        text = text.strip()

        return text.startswith(
            (
                "[FOOTNOTE]",
                "[FORMULA PLACEHOLDER]",
                "[TABLE CAPTION]",
                "[FIGURE CAPTION]",
            )
        )



    def chunk(self):

        markdown = self.markdown_file.read_text(encoding="utf-8")

        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
                ("####", "Header_4"),
                ("#####", "Header_5"),
            ])

        header_docs = splitter.split_text(markdown)
        print(f"Context-aware splits: {len(header_docs)}")

        # Tag footnotes

        for doc in header_docs:
            lines = doc.page_content.split("\n")

            lines = [
                re.sub(
                    r"^(\d+|[^\w\s])\s+[A-Z]",
                    lambda m: "[FOOTNOTE]: " + m.group(0),
                    line,
                )
                for line in lines
            ]

            doc.page_content = "\n".join(lines)

        # Merge broken paragraphs

        for doc in header_docs:
            lines = doc.page_content.split("\n")
            delete = []
            for i in range(len(lines)):
                if i in delete:
                    lines[i] = ""
                    delete.remove(i)
                    continue
                complete = lines[i].strip().endswith((".", "!", "?"))

                if complete or self._is_special(lines[i]):
                    continue

                for j in range(i + 1, len(lines)):
                    if self._is_special(lines[j]):
                        continue

                    lines[i] = (lines[i] + " " + lines[j])
                    lines[i] = re.sub(r"\s+", " ", lines[i])
                    delete.append(j)
                    break

            lines = [x for x in lines if x]

            doc.page_content = "\n".join(lines)

        # Recursive chunking

        recursive_splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=450,
                chunk_overlap=100,
                separators=[
                    "\n\n",
                    "\n",
                    ".",
                    " ",
                ],
            )
        )

        chunks = recursive_splitter.split_documents(header_docs)
        print(f"Final chunks: {len(chunks)}")

        # Convert to DataFrame

        rows = []

        for idx, chunk in enumerate(chunks):

            rows.append(
                {
                    "chunk_id": idx,
                    "content": chunk.page_content,
                    "text_length": len(chunk.page_content),
                    "source": self.project_dir.name,
                    "header_1": chunk.metadata.get(
                        "Header_1", ""
                    ),
                    "header_2": chunk.metadata.get(
                        "Header_2", ""
                    ),
                    "header_3": chunk.metadata.get(
                        "Header_3", ""
                    ),
                    "header_4": chunk.metadata.get(
                        "Header_4", ""
                    ),
                    "header_5": chunk.metadata.get(
                        "Header_5", ""
                    ),
                    "metadata": chunk.metadata,
                }
            )

        df = pd.DataFrame(rows)

        DATABASE_URL = (
            "postgresql://prism:prism123@postgres:5432/prism"
        )

        engine = create_engine(DATABASE_URL)

        df.to_sql(
            "document_chunks",
            engine,
            if_exists="append",
            index=False,
        )

        print(f"Saved {len(df)} chunks.")

        return df