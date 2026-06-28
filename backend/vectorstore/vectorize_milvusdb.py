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

from sqlalchemy import create_engine
import pandas as pd

##########################################################################
# Configuration
##########################################################################

EMBEDDING_MODEL = "nomic-embed-text-v2-moe"
EMBEDDING_DIM = 768

MILVUS_HOST = "milvus"
MILVUS_PORT = 19530

DATABASE_URL = (
    "postgresql://prism:prism123@postgres:5432/prism"
)

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
        project_name: str,
        db_name: str,
        collection_name: str,
        replace_collection: bool = False,
    ):

        self.project_name = project_name
        self.db_name = db_name
        self.collection_name = collection_name
        self.replace_collection = replace_collection

        self.embedding_model = OllamaEmbeddings(
            model=EMBEDDING_MODEL
        )

    ######################################################################

    def vectorize(self):

        chunks = self._load_chunks()

        print(f"Loaded {len(chunks)} chunks.")

        self._connect()

        collection = self._prepare_collection()

        self._insert(collection, chunks)

        print("Vectorization complete.")

    ######################################################################

    def _load_chunks(self):

        engine = create_engine(DATABASE_URL)

        query = f"""
        SELECT
            chunk_id,
            source_file,
            header_1,
            header_2,
            header_3,
            header_4,
            header_5,
            content
        FROM document_chunks
        WHERE project_name='{self.project_name}'
        ORDER BY chunk_id
        """

        return pd.read_sql(query, engine)

    ######################################################################

    def _connect(self):

        connections.connect(
            host=MILVUS_HOST,
            port=MILVUS_PORT,
        )

        if self.db_name not in db.list_database():
            db.create_database(self.db_name)

        db.using_database(self.db_name)

    ######################################################################

    def _prepare_collection(self):

        if (
            self.collection_name in utility.list_collections()
            and self.replace_collection
        ):
            utility.drop_collection(self.collection_name)

        if self.collection_name in utility.list_collections():
            return Collection(self.collection_name)

        schema = CollectionSchema(
            fields=[
                FieldSchema(
                    name="chunk_id",
                    dtype=DataType.INT64,
                    is_primary=True,
                ),
                FieldSchema(
                    name="source",
                    dtype=DataType.VARCHAR,
                    max_length=500,
                ),
                FieldSchema(
                    name="header_1",
                    dtype=DataType.VARCHAR,
                    max_length=255,
                ),
                FieldSchema(
                    name="header_2",
                    dtype=DataType.VARCHAR,
                    max_length=255,
                ),
                FieldSchema(
                    name="header_3",
                    dtype=DataType.VARCHAR,
                    max_length=255,
                ),
                FieldSchema(
                    name="header_4",
                    dtype=DataType.VARCHAR,
                    max_length=255,
                ),
                FieldSchema(
                    name="header_5",
                    dtype=DataType.VARCHAR,
                    max_length=255,
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=EMBEDDING_DIM,
                ),
                FieldSchema(
                    name="content",
                    dtype=DataType.VARCHAR,
                    max_length=8192,
                ),
            ]
        )

        collection = Collection(
            name=self.collection_name,
            schema=schema,
        )

        collection.create_index(
            field_name="embedding",
            index_params=INDEX_PARAMS,
        )

        collection.load()

        return collection

    ######################################################################

    def _insert(
        self,
        collection,
        chunks: pd.DataFrame,
    ):

        embeddings = self.embedding_model.embed_documents(
            chunks["content"].tolist()
        )

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

        print(
            f"Inserted {collection.num_entities} vectors."
        )

    ######################################################################

    def search(
        self,
        query,
        top_k=5,
    ):

        db.using_database(self.db_name)

        collection = Collection(self.collection_name)

        collection.load()

        query_embedding = self.embedding_model.embed_query(query)

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=INDEX_PARAMS,
            limit=top_k,
            output_fields=[
                "chunk_id",
                "source",
                "header_1",
                "header_2",
                "header_3",
                "header_4",
                "header_5",
                "content",
            ],
        )

        return results