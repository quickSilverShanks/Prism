CREATE TABLE document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    source_file VARCHAR(500) NOT NULL,
    header_1 VARCHAR(255),
    header_2 VARCHAR(255),
    header_3 VARCHAR(255),
    header_4 VARCHAR(255),
    header_5 VARCHAR(255),
    content TEXT NOT NULL,
    text_length INT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);