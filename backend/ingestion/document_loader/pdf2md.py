import copy
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

from langchain_docling.loader import DoclingLoader, ExportType

# Disable symlinks (Docling on Windows)
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

EXPORT_TYPE = ExportType.MARKDOWN



class PDFParser:
    """
    Parses a PDF into cleaned Markdown and extracts tables, figures and metadata for downstream processing.
    """

    def __init__(self, pdf_path: str, output_root: str):

        self.pdf_path = Path(pdf_path)
        self.project_name = self.pdf_path.stem
        self.output_root = Path(output_root) / self.project_name

        self.markdown_dir = self.output_root / "markdown"
        self.tables_dir = self.output_root / "tables"
        self.figures_dir = self.output_root / "figures"
        self.metadata_dir = self.output_root / "metadata"

        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)



    def parse(self):

        # initiate data parse
        docs = self._extract_markdown()

        # total paragraphs(separation by '\n\n', including footnotes, table and image captions)
        paragraphs = docs[0].page_content.split("\n\n")
        # print("Total parsed paragraphs:", len(paragraphs))

        # preprocess the parsed markdown to make it easy to identify different elements like (sub)headings, tables, images, footnotes etc
        parsed_markdown, tables, figures = self._preprocess(paragraphs)

        # assign the modified page content back to document
        docs[0].page_content = "\n\n".join(parsed_markdown)

        self._save_outputs(
            markdown=docs[0].page_content,
            tables=tables,
            figures=figures,
            metadata={
                "source": str(self.pdf_path),
                "project": self.project_name,
                "paragraphs": len(parsed_markdown),
                "file_size_bytes": self.pdf_path.stat().st_size,
                "parsed_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        return docs



    def _extract_markdown(self):

        # print("Importing pdf file: ", self.pdf_path)
        loader = DoclingLoader(file_path=str(self.pdf_path), export_type=EXPORT_TYPE)
        docs = loader.load()
        # print(f"Loaded {len(docs)} document(s).")
        return docs



    def _remove_false_headings(self, parsed_content):

        # extract headings with index
        headings = [(i, text) for i, text in enumerate(parsed_content) if text.strip().startswith("#")]

        # find numbered headings
        numbered = [
            idx for idx, text in headings
            if re.match(r"^#+\s+\d+", text.strip())
            ]

        if not numbered:
            return parsed_content   # nothing to process

        first_num = min(numbered)
        last_num = max(numbered)

        # remove '#' for unnumbered headings in between
        for idx, text in headings:
            stripped = text.strip()
            is_numbered = bool(re.match(r"^#+\s+\d+", stripped))
            if first_num < idx < last_num and not is_numbered:
                # remove leading hashes, don't keep text as it could be incorrectly captured from some image
                parsed_content[idx] = ""
                # use below line instead to remove hashes but keep the text
                # parsed_content[idx] = re.sub(r'^#+\s*', '', text)

        return parsed_content



    def _preprocess(self, paragraphs):

        parsed = copy.deepcopy(paragraphs)

        parsed_tables = {}
        parsed_figures = {}

        # create heading:sub-heading(s) hierarchy
        parsed = [re.sub(r"^#+", "#", text) for text in parsed]
        parsed = [
            re.sub(
                r"# (\d+(?:\.\d+){0,5}) ",
                lambda m: "#" * (m.group(1).count(".") + 1) + " " + m.group(1) + " ", text
                )
                for text in parsed
            ]

        # remove false headings, like something captured with a hash but is infact just a text around/in some figure
        parsed = self._remove_false_headings(parsed)

        # replace formula decode error with placeholder
        parsed = [text.replace("<!-- formula-not-decoded -->", "[FORMULA PLACEHOLDER]") for text in parsed]


        # extract table and table number, and tag table captions
        for i, line in enumerate(parsed):
            if not line.startswith("|"):
                continue

            prev_line = parsed[i - 1] if i > 0 else ""
            next_line = parsed[i + 1] if i < len(parsed) - 1 else ""

            caption = None

            if prev_line.lower().startswith("table "):
                caption = i - 1
            elif next_line.lower().startswith("table "):
                caption = i + 1

            if caption is not None:
                title = parsed[caption].split(":")[0]
                parsed_tables[title] = line
                parsed[caption] = ("[TABLE CAPTION]: " + parsed[caption])
            else:
                parsed_tables.setdefault("Untitled", []).append(line)

            parsed[i] = ""
        
        parsed = [text for text in parsed if text != ""]


        # tag figure captions
        for i, text in enumerate(parsed):
            if text.lower().startswith("figure "):
                parsed_figures[f"Figure {len(parsed_figures)+1}"] = text
                parsed[i] = "[FIGURE CAPTION]: " + text


        return parsed, parsed_tables, parsed_figures



    def _save_outputs(self, markdown, tables, figures, metadata):

        with open(self.markdown_dir / f"{self.project_name}.md", "w", encoding="utf-8",) as f:
            f.write(markdown)

        with open(self.tables_dir / "tables.json", "w", encoding="utf-8",) as f:
            json.dump(tables, f, indent=2, ensure_ascii=False)

        with open(self.figures_dir / "figures.json", "w", encoding="utf-8",) as f:
            json.dump(figures, f, indent=2, ensure_ascii=False)

        with open(self.metadata_dir / "metadata.json", "w", encoding="utf-8",) as f:
            json.dump(metadata, f, indent=2)

        # print(f"Project saved to {self.output_root}")