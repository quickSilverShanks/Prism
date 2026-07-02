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

    def __init__(self, project_name: str, data_dir: str, export:bool = True):

        self.data_dir = Path(data_dir)
        self.project_name = project_name
        self.export = export

        self.markdown_dir = self.data_dir / "markdown"
        self.markdown_file = self.markdown_dir / f"{self.project_name}.md"

        self.output_dir = self.data_dir / "chunks"
        self.output_dir.mkdir(parents=True, exist_ok=True)



    @staticmethod
    def _is_special(text):

        text = text.strip()
        return text.startswith(('[FOOTNOTE]', '[FORMULA PLACEHOLDER]', '[TABLE CAPTION]', '[FIGURE CAPTION]'))



    def chunk(self):

        doc_markdown = self.markdown_file.read_text(encoding="utf-8")

        # use context aware splitting to get heading and subheadings in separate documents with respective metadata
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
                ("####", "Header_4"),
                ("#####", "Header_5"),
            ])

        header_docs = splitter.split_text(doc_markdown)
        # print(f"Total context-aware splits: {len(header_docs)}")


        # tag the footnotes
        for doc in header_docs:
            content_subsplit = doc.page_content.split("\n")
            content_subsplit = [
                re.sub(
                    r"^(\d+|[^\w\s])\s+[A-Z]",
                    lambda m: "[FOOTNOTE]: " + m.group(0),
                    text
                )
                for text in content_subsplit
            ]
            doc.page_content = "\n".join(content_subsplit)


        # merge sentences/paragraphs broken midway due to page change and move footnotes and captions after the paragraph ends
        for doc in header_docs:
            content_subsplit = doc.page_content.split("\n")
            joined_deletion = []

            for i in range(len(content_subsplit)):
                if i in joined_deletion:
                    content_subsplit[i] = ""
                    joined_deletion.remove(i)
                    continue

                complete_flag = content_subsplit[i].strip().endswith((".", "!", "?"))
                if complete_flag or self._is_special(content_subsplit[i]):
                    continue
                elif i < len(content_subsplit)-1:
                    for inext in range(i + 1, len(content_subsplit)):
                        if self._is_special(content_subsplit[inext]):
                            continue
                        else:
                            content_subsplit[i] = (content_subsplit[i] + " " + content_subsplit[inext])
                            content_subsplit[i] = re.sub(r"\s+", " ", content_subsplit[i])
                            joined_deletion.append(inext)
                            break
                else:
                    continue

            content_subsplit = [text for text in content_subsplit if text != ""]
            doc.page_content = "\n".join(content_subsplit)


        # print/log sentence structure in each split
        # for doc in header_docs:
        #     para_count = len(doc.page_content.split('\n'))
        #     print(f"No. of Characters, Words, Sentences and Paragraphs: {len(doc.page_content)}, {len(doc.page_content.split(' '))}, {len(doc.page_content.split('.'))}, {para_count} \t||  Metadata: {doc.metadata}")


        # recursive chunking with overlap within all the sub-headings; try to keep paragraphs, sentences, words intact in this same order of preference
        recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=450,
                chunk_overlap=100,  # overlap may not be frequent and easy to find as its going to prioritize the separators first
                separators=[
                    "\n\n",     # if any remain
                    "\n",       # paragraph boundary
                    ".",        # sentence boundary
                    " ",        # fallback, word boundary
                ]
            )

        final_split_docs = recursive_splitter.split_documents(header_docs)
        # print(f"Total final document splits created: {len(final_split_docs)}")


        # export final split docs
        if self.export:
            rows = []
            for idx, chunk in enumerate(final_split_docs):
                rows.append(
                    {
                        "chunk_id": idx,
                        "content": chunk.page_content,
                        "text_length": len(chunk.page_content),
                        "source": self.project_name,
                        "header_1": chunk.metadata.get("Header_1", ""),
                        "header_2": chunk.metadata.get("Header_2", ""),
                        "header_3": chunk.metadata.get("Header_3", ""),
                        "header_4": chunk.metadata.get("Header_4", ""),
                        "header_5": chunk.metadata.get("Header_5", ""),
                        "metadata": chunk.metadata,     # putting entire metadata together as well, for brevity
                    }
                )
            df = pd.DataFrame(rows)

            output_file = self.output_dir / f"{self.project_name}.json"
            df.to_json(output_file, orient="records", indent=4)
            # print(f"Saved {len(df)} chunks to {output_file}.")

        return final_split_docs