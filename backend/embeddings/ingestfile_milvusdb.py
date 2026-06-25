import pandas as pd
import json
import re
import copy
import os
import argparse

from langchain_docling.loader import DoclingLoader, ExportType

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ollama import OllamaEmbeddings

from langchain_milvus import Milvus
from pymilvus import connections, db, utility, Collection, CollectionSchema, FieldSchema, DataType

# disable symlinks with env variable so that loader.load() with docling works
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

EXPORT_TYPE = ExportType.MARKDOWN
INPUT_DATA_LOC = "../data/pdfs/"
OTHER_DATA_LOC = "../data/others/"
EMBEDDING_MODEL = "nomic-embed-text-v2-moe"
EMBEDDING_DIM = 768
MILVUS_HOST = 'localhost'
MILVUS_PORT = 19530

INDEX_PARAMS = {
    'metric_type': 'L2',
    'index_type': 'HNSW',
    'params': {
        'M': 16,
        'efConstruction': 100
    }
}


def extract_markdown():
    print("Importing pdf file: ", FILE_PATH)
    loader = DoclingLoader(file_path=FILE_PATH, export_type=EXPORT_TYPE)
    docs = loader.load()
    print("Total documents extracted: ", len(docs))
    return docs



def remove_false_headings(parsed_content):
    # extract headings with index
    headings = [(i, text) for i, text in enumerate(parsed_content) if text.strip().startswith('#')]

    # find numbered headings
    numbered_idxs = [
        idx for idx, text in headings
        if re.match(r'^#+\s+\d+', text.strip())
    ]

    if not numbered_idxs:
        return parsed_content  # nothing to process

    first_num = min(numbered_idxs)
    last_num = max(numbered_idxs)

    # remove '#' for unnumbered headings in between
    for idx, text in headings:
        stripped = text.strip()
        is_numbered = bool(re.match(r'^#+\s+\d+', stripped))
        if first_num < idx < last_num and not is_numbered:
            # remove leading hashes, don't keep text as it could be incorrectly captured from some image
            parsed_content[idx] = ''
            # use below line instead to remove hashes but keep the text
            # parsed_content[idx] = re.sub(r'^#+\s*', '', text)

    return parsed_content



def initial_preprocess_markdown(doc_paragraphs, tables_json):
    # initialize parsed content and extracted tables
    parsed_content = copy.deepcopy(doc_paragraphs)
    parsed_tables = {}


    # create heading:sub-heading(s) hierarchy
    parsed_content = [re.sub(r'^#+', '#', text) for text in parsed_content]
    parsed_content = [
        re.sub(
            r'# (\d+(?:\.\d+){0,5}) ',
            lambda m: '#' * (m.group(1).count('.') + 1) + ' ' + m.group(1) + ' ',
            text
        )
        for text in parsed_content
    ]


    # remove false headings, like something captured with a hash but is infact just a text around/in some figure
    parsed_content = remove_false_headings(parsed_content)


    # replace formula decode error with placeholder
    parsed_content = [text.replace('<!-- formula-not-decoded -->', '[FORMULA PLACEHOLDER]') for text in parsed_content]


    # extract table and table number, and tag table captions
    for i, line in enumerate(parsed_content):
        if not line.startswith('|'):
            continue

        prev_line = parsed_content[i-1] if i > 0 else ""
        next_line = parsed_content[i+1] if i < len(parsed_content) - 1 else ""

        caption_line = None

        if prev_line.lower().startswith('table '):
            caption_line = i - 1
        elif next_line.lower().startswith('table '):
            caption_line = i + 1

        if caption_line is not None:
            title = parsed_content[caption_line].split(':')[0]
            parsed_tables[title] = line
            parsed_content[caption_line] = "[TABLE CAPTION]: " + parsed_content[caption_line]
        else:
            title = "Untitled"
            parsed_tables.setdefault(title, []).append(line)

        parsed_content[i] = ''

    parsed_content = [text for text in parsed_content if text != ""]


    # tag figure captions
    parsed_content = [
        "[FIGURE CAPTION]: " + text if text.lower().startswith("figure ") else text
        for text in parsed_content
    ]


    # export parsed tables to load later when needed
    os.makedirs(OTHER_DATA_LOC, exist_ok=True)
    with open(os.path.join(OTHER_DATA_LOC, tables_json), "w", encoding="utf-8") as f:
        json.dump(parsed_tables, f, indent=2, ensure_ascii=False)


    return parsed_content



def is_special(text):
    text = text.strip()
    return text.startswith(('[FOOTNOTE]', '[FORMULA PLACEHOLDER]', '[TABLE CAPTION]', '[FIGURE CAPTION]'))



def split_preprocess_markdown(docs, parsed_md):
    # use context aware splitting to get heading and subheadings in separate documents with respective metadata
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3"),
            ("####", "Header_4"),
            ("#####", "Header_5"),
        ],
        )

    splits = [split for doc in docs for split in splitter.split_text(doc.page_content)]
    print("Total Context Aware Splits:", len(splits))


    # tag the footnotes
    for s in splits:
        content_subsplit = s.page_content.split("\n")
        content_subsplit = [
            re.sub(
                r'^(\d+|[^\w\s])\s+[A-Z]',
                lambda m: "[FOOTNOTE]: " + m.group(0),
                text
            )
        for text in content_subsplit
        ]
        s.page_content = '\n'.join(content_subsplit)


    # merge sentences/paragraphs broken midway due to page change and move footnotes and captions after the paragraph ends
    for s in splits:
        content_subsplit = s.page_content.split("\n")
        joined_deletion = []

        for i in range(len(content_subsplit)):
            if i in joined_deletion:
                content_subsplit[i] = ''
                joined_deletion.remove(i)
                continue
            complete_flag = content_subsplit[i].strip().endswith(('.', '?', '!'))
            if complete_flag or is_special(content_subsplit[i]):
                continue
            elif i < len(content_subsplit)-1:
                for next in range(i+1, len(content_subsplit)):
                    if is_special(content_subsplit[next]):
                        continue
                    else:
                        content_subsplit[i] = content_subsplit[i] + " " + content_subsplit[next]
                        content_subsplit[i] = re.sub(r'\s+', ' ', content_subsplit[i])
                        joined_deletion.append(next)
                        break
            else:
                continue

        content_subsplit = [text for text in content_subsplit if text != ""]
        s.page_content = '\n'.join(content_subsplit)


    # print/log sentence structure in each split
    for s in splits:
        para_count = len(s.page_content.split('\n'))
        print(f"No. of Characters, Words, Sentences and Paragraphs: {len(s.page_content)}, {len(s.page_content.split(' '))}, {len(s.page_content.split('.'))}, {para_count} \t||  Metadata: {s.metadata}")


    # recursive chunking with overlap within all the sub-headings; try to keep paragraphs, sentences, words intact in this same order of preference
    r_splitter = RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=100,  # overlap may not be frequent and easy to find as its going to prioritize the separators first.
        separators=[
            "\n\n",   # if any remain
            "\n",     # paragraph boundary
            ".",     # sentence boundary
            " ",      # fallback, word boundary
        ]
    )

    final_split_docs = r_splitter.split_documents(splits)
    print(f"Total final documents created: {len(final_split_docs)}")


    # export final split structure for investigation if needed
    split_n, metadata_list, textlen_list = [], [], []

    for i, sdoc in enumerate(final_split_docs):
        split_n.append(i)
        metadata_list.append(sdoc.metadata)
        textlen_list.append(len(sdoc.page_content))

    doc_split_structure = pd.DataFrame({'SplitNumber': split_n, 'Metadata':metadata_list, 'TextLength': textlen_list})
    doc_split_structure['DocName'] = FILE_PATH
    doc_split_structure.to_csv(OTHER_DATA_LOC + "doc_split_structure.csv")
    

    return final_split_docs



def create_vectordb_milvus(final_split_docs, dbname, dbreplace, collname):
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    em = embeddings.embed_query("test")
    print("Dimension of embedding vector:", len(em))


    conn = connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    print("Available databases in Milvus Server:", db.list_database())


    if dbname not in db.list_database():
        db.create_database(dbname)
        print(f"Database {dbname} created")
    elif dbreplace:
        print(f"Replacing existing DB {dbname}...")
        db.using_database(dbname)

        # drop all collections
        collections = utility.list_collections()

        for col in collections:
            utility.drop_collection(col)
            print(f"Dropped collection: {col}")

        # switch to default (optional but safer) and then drop the db
        db.using_database("default")
        db.drop_database(dbname)
        print(f"Dropped database: {dbname}")
        db.create_database(dbname)
        print(f"Database {dbname} created")
    else:
        print("Keeping existing DBs...")


    db.using_database(dbname)
    if collname in utility.list_collections():
        utility.drop_collection(collname)
        print(f"Dropped existing collection {col} from database {dbname}")


    # schema definition for new collection with id_field as primary key
    id_field = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
    source_field = FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=255)
    header_1_field = FieldSchema(name="header_1", dtype=DataType.VARCHAR, max_length=255)
    header_2_field = FieldSchema(name="header_2", dtype=DataType.VARCHAR, max_length=255)
    header_3_field = FieldSchema(name="header_3", dtype=DataType.VARCHAR, max_length=255)
    header_4_field = FieldSchema(name="header_4", dtype=DataType.VARCHAR, max_length=255)
    header_5_field = FieldSchema(name="header_5", dtype=DataType.VARCHAR, max_length=255)
    embedding_field = FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    content_field = FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2048)
    
    # combine fields into a schema
    schema = CollectionSchema(
        fields=[id_field, source_field, header_1_field, header_2_field, header_3_field, header_4_field, header_5_field, embedding_field, content_field],
        description="Arxiv documents collection schema"
    )


    # initialize the collection with the schema
    collection = Collection(name=collname, schema=schema)
    print(f"Collection {collname} created in database {dbname}")


    # create index
    collection.create_index(field_name='embeddings', index_params=INDEX_PARAMS)
    print("Index created in the collection")

    collection.load()


    # inserting data into collections
    sources = [FILE_PATH]*len(final_split_docs)
    headers1 = [chunk.metadata.get('Header_1', '') for chunk in final_split_docs]
    headers2 = [chunk.metadata.get('Header_2', '') for chunk in final_split_docs]
    headers3 = [chunk.metadata.get('Header_3', '') for chunk in final_split_docs]
    headers4 = [chunk.metadata.get('Header_4', '') for chunk in final_split_docs]
    headers5 = [chunk.metadata.get('Header_5', '') for chunk in final_split_docs]
    page_contents = [chunk.page_content for chunk in final_split_docs]
    content_embeddings = embeddings.embed_documents(page_contents)

    # the order must match: [source_field, header_1_field, header_2_field, header_3_field, header_4_field, header_5_field, embedding_field, content_field]
    collection.insert([
        sources, headers1, headers2, headers3, headers4, headers5, content_embeddings, page_contents
        ])
    
    collection.flush()
    print(f"Total entities inserted in the collection {collname}: {collection.num_entities}")
    print("The VectorDB is ready to be queried.")



def search_milvus(dbname, collname, query, k):
    # set up embedding model and query
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    query_embedding = embeddings.embed_query(query)

    # load the required collection
    conn = connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    db.using_database(dbname)
    collection = Collection(name=collname)
    collection.load()

    results = collection.search(
        data= [query_embedding],
        anns_field= 'embeddings',
        param= INDEX_PARAMS,    # could be different as well (perhaps)
        limit= k,
        output_fields= ['source', 'header_1', 'header_2', 'header_3', 'header_4', 'header_5', 'content']
    )

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A script to chunk pdf documents and create Milvus vectorDB.")
    parser.add_argument("--mode", required=True, choices=['parse', 'retrieve'], default='parse', help="Select the operational mode, parse or retrieve.")
    parser.add_argument("--filename", help="Name of pdf file, without extension, stored in data/pdfs/ location.")
    parser.add_argument("--tables_json", help="Name of tables json file, with extension, that will be save in data/others/ location.")
    parser.add_argument("--split_structure", help="Name of final split structure csv file, without extension, that will be save in data/others/ location.")
    parser.add_argument("--dbname", help="Name of the Milvus database.")
    parser.add_argument("--dbreplace", action="store_true", help="Replace old db with same name if flag is provided.")
    parser.add_argument("--collname", help="Name of the collection to be created, within Milvus database, will be replaced if exists.")
    parser.add_argument("--query", help="User query to do retrieval from vectordb.")
    parser.add_argument("--k", type=int, default=5, help="Total retrievalsto fetch from vectordb.")
    args = parser.parse_args()

    if args.mode == 'parse':
        if not (args.filename and args.tables_json and args.split_structure and args.dbname and args.collname):
            raise SystemError("Please provide all the required information to proceed: filename, tables_json, split_structure, dbname, collname.")
    
        print("Initiated Data Parse ...")
        FILE_PATH = INPUT_DATA_LOC + args.filename +  ".pdf"

        docs = extract_markdown()

        # total paragraphs(separation by '\n\n', including footnotes, table and image captions)
        doc_paragraphs = docs[0].page_content.split('\n\n')
        print("Total parsed paragraphs:", len(doc_paragraphs))

        # preprocess the parsed markdown to make it easy to identify different elements like (sub)headings, tables, images, footnotes etc
        parsed_content = initial_preprocess_markdown(doc_paragraphs, args.tables_json)

        # assign the modified page content back to document
        docs[0].page_content = '\n\n'.join(parsed_content)

        # split document into useful chunks
        final_split_docs = split_preprocess_markdown(docs, args.split_structure)

        # create vectorDB from chunks
        create_vectordb_milvus(final_split_docs, args.dbname, args.dbreplace, args.collname)
        print("Data Parse Completed!")
    else:
        if not (args.dbname and args.collname and args.query):
            raise SystemError("Please provide all the required information to proceed: dbname, collname, query.")

        print("Initiated Data Retrieval ...")
        retrieved_docs = search_milvus(args.dbname, args.collname, args.query, args.k)

        # print retrieved documents
        for i in range(args.k):
            print(f"Retrieved Document {i+1}:")
            print(retrieved_docs[0][i])
            print("--------------------------------------------------")
        print("Data Retrieval Compelted!")