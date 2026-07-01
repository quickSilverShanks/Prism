from pymilvus import (
    connections,
    db,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)

from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL')

MILVUS_HOST = os.getenv('MILVUS_HOST')
MILVUS_PORT = int(os.getenv('MILVUS_PORT'))

INDEX_PARAMS = {
    "metric_type": "L2",
    "index_type": "HNSW",
    "params": {
        "M": 16,
        "efConstruction": 100,
    },
}


class Vectorizer:

    def __init__(
        self,
        data_dir: str,
        project_name: str,
        db_name: str,
        replace_collection: bool = False,
        replace_db: bool = False
    ):
        self.data_dir = Path(data_dir)
        self.project_name = project_name
        self.db_name = db_name
        self.collection_name = project_name
        self.replace_collection = replace_collection
        self.replace_db = replace_db
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.auto_id = True



    def vectorize(self, split_docs=None):
        if split_docs is None:
            json_path = self.data_dir / "chunks" / f"{self.project_name}.json"
            chunks = self._create_doc(json_path)
        else:
            self.auto_id = False
        # print(f"Loaded {chunks.shape[0]} chunks for embedding.")

        self._connect()
        collection = self._prepare_collection()
        self._insert(collection, chunks)
        # print("Vectorization complete.")



    def _create_doc(self, json_path: str):
        "This method should take json file as input and create langchain Document with proper metadata and page_content"
        pass



    def _get_embedding_dim(self):
        embedding = self.embedding_model.embed_query("test")
        return len(embedding)



    def _connect(self):
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        # print("Available databases in Milvus Server:", db.list_database())

        if self.db_name not in db.list_database():
            db.create_database(self.db_name)
            # print(f"Database {self.db_name} created")
        elif self.replace_db:
            # print(f"Replacing existing DB {self.db_name}...")
            db.using_database(self.db_name)

            # drop all collections
            collections = utility.list_collections()

            for col in collections:
                utility.drop_collection(col)
                # print(f"Dropped collection: {col}")

            # switch to default (optional but safer) and then drop the db
            db.using_database("default")
            db.drop_database(self.db_name)
            # print(f"Dropped database: {self.db_name}")
            db.create_database(self.db_name)
            # print(f"Database {self.db_name} created")
        else:
            # print("Keeping existing DBs...")
            pass



    def _prepare_collection(self):
        db.using_database(self.db_name)
        if self.collection_name in utility.list_collections() and self.replace_collection:
            utility.drop_collection(self.collection_name)
            # print(f"Dropped existing collection {self.collection_name} from database {self.db_name}")

        if self.collection_name in utility.list_collections():
            return Collection(self.collection_name)

        # schema for new collection with id_field as primary key
        schema = CollectionSchema(
            fields=[
                FieldSchema(name="chunk_id", dtype=DataType.INT64, is_primary=True, auto_id=self.auto_id),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="header_1", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_2", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_3", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_4", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_5", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._get_embedding_dim())
            ],
            # description="Document"
        )

        # initialize the collection with the schema
        collection = Collection(name=self.collection_name, schema=schema)
        # print(f"Collection {self.collection_name} created in database {self.db_name}")

        # create index
        collection.create_index(field_name="embedding", index_params=INDEX_PARAMS)
        # print("Index created for the collection {self.collection_name}")

        collection.load()

        return collection



    def _insert(self, collection, chunks: Document):
        # inserting data into collections, batch mode will be added in future
        sources = [self.project_name]*len(chunks)
        headers1 = [c.metadata.get('Header_1', '') for c in chunks]
        headers2 = [c.metadata.get('Header_2', '') for c in chunks]
        headers3 = [c.metadata.get('Header_3', '') for c in chunks]
        headers4 = [c.metadata.get('Header_4', '') for c in chunks]
        headers5 = [c.metadata.get('Header_5', '') for c in chunks]
        page_contents = [c.page_content for c in chunks]
        content_embeddings = self.embedding_model.embed_documents(page_contents)

        collection.insert([
            sources, headers1, headers2, headers3, headers4, headers5, page_contents, content_embeddings
            ])
        
        collection.flush()
        # print(f"Total entities inserted in the collection {self.collection_name}: {collection.num_entities}")
        # print("The VectorDB is ready to be queried.")



    def search(self, query: str, top_k: int = 5):
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        # print("Available databases in Milvus Server:", db.list_database())
        db.using_database(self.db_name)
        collection = Collection(self.collection_name)
        collection.load()

        query_embedding = self.embedding_model.embed_query(query)

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=INDEX_PARAMS,
            limit=top_k,
            output_fields=["chunk_id", "source", "header_1", "header_2", "header_3", "header_4", "header_5", "content"]
        )

        return results