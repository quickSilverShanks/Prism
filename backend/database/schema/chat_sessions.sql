CREATE TABLE chat_sessions (
    session_id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(project_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);