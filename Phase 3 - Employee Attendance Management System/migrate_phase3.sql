USE employee_attendance_db;

CREATE TABLE IF NOT EXISTS token_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    refresh_jti VARCHAR(36) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_token_sessions_user_id (user_id),

    CONSTRAINT fk_token_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);