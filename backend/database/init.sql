-- Create database (run while connected to the default 'postgres' database)
CREATE DATABASE prism;

-- Connect to the new database
\c prism;

-- Create all tables
\i schema/projects.sql
\i schema/document_chunks.sql
\i schema/chat_sessions.sql