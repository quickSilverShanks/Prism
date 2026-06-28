-- Create database (run while connected to the default 'postgres' database)
CREATE DATABASE prism;

-- Connect to the new database
\c prism;

-- Create tables
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(project_id),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_sessions (
    session_id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(project_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);