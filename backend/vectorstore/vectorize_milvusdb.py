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

from pathlib import Path
import pandas as pd
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
    ):
        
        self.data_dir = Path(data_dir)
        self.project_name = project_name
        self.db_name = db_name
        self.collection_name = project_name
        self.replace_collection = replace_collection
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)



    def vectorize(self, split_docs=None):

        if split_docs is None:
            json_path = self.data_dir / "chunks" / f"{self.project_name}.json"
            chunks = pd.read_json(json_path)
        else:
            rows = []
            for idx, chunk in enumerate(split_docs):
                rows.append(
                    {
                        "chunk_id": idx,
                        "content": chunk.page_content,
                        "source": self.project_name,
                        "header_1": chunk.metadata.get("Header_1", ""),
                        "header_2": chunk.metadata.get("Header_2", ""),
                        "header_3": chunk.metadata.get("Header_3", ""),
                        "header_4": chunk.metadata.get("Header_4", ""),
                        "header_5": chunk.metadata.get("Header_5", ""),
                    }
                )
            chunks = pd.DataFrame(rows)

        # print(f"Loaded {chunks.shape[0]} chunks for embedding.")
        self._connect()
        collection = self._prepare_collection()
        self._insert(collection, chunks)
        # print("Vectorization complete.")



    def _get_embedding_dim(self):

        embedding = self.embedding_model.embed_query("test")
        return len(embedding)



    def _connect(self):

        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        if self.db_name not in db.list_database():
            db.create_database(self.db_name)
        db.using_database(self.db_name)



    def _prepare_collection(self):

        if self.collection_name in utility.list_collections() and self.replace_collection:
            utility.drop_collection(self.collection_name)

        if self.collection_name in utility.list_collections():
            return Collection(self.collection_name)

        schema = CollectionSchema(
            fields=[
                FieldSchema(name="chunk_id", dtype=DataType.INT64, is_primary=True),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="header_1", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_2", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_3", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_4", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="header_5", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self._get_embedding_dim()),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192)
            ]
        )

        collection = Collection(name=self.collection_name, schema=schema)
        collection.create_index(field_name="embedding", index_params=INDEX_PARAMS)
        collection.load()

        return collection



    def _insert(self, collection, chunks: pd.DataFrame):

        embeddings = self.embedding_model.embed_documents(chunks["content"].tolist())

        collection.insert(
            [
                chunks["chunk_id"].tolist(),
                chunks["source_file"].tolist(),
                chunks["header_1"].fillna("").tolist(),
                chunks["header_2"].fillna("").tolist(),
                chunks["header_3"].fillna("").tolist(),
                chunks["header_4"].fillna("").tolist(),
                chunks["header_5"].fillna("").tolist(),
                embeddings,
                chunks["content"].tolist(),
            ]
        )

        collection.flush()
        # print(f"Inserted {collection.num_entities} vectors.")



    def search(self, query, top_k=5):

        db.using_database(self.db_name)
        collection = Collection(self.collection_name)
        collection.load()
        query_embedding = self.embedding_model.embed_query(query)

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=INDEX_PARAMS,
            limit=top_k,
            output_fields=["chunk_id", "source", "header_1", "header_2", "header_3", "header_4", "header_5", "content",],
        )

        return results