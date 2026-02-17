-- 008_best-ecomerce-review Database Schema (PostgreSQL)
CREATE TABLE IF NOT EXISTS raw_reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(100) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_date DATE NOT NULL,
    review_content TEXT NOT NULL,
    rating DECIMAL(2,1),
    author_masked VARCHAR(50),
    product_category VARCHAR(100),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cleaned_reviews (
    id SERIAL PRIMARY KEY,
    raw_review_id INTEGER NOT NULL,
    review_content_cleaned TEXT NOT NULL,
    char_length INTEGER NOT NULL,
    has_emoji BOOLEAN DEFAULT FALSE,
    has_profanity BOOLEAN DEFAULT FALSE,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_review_id) REFERENCES raw_reviews(id)
);

CREATE TABLE IF NOT EXISTS scored_reviews (
    id SERIAL PRIMARY KEY,
    cleaned_review_id INTEGER NOT NULL,
    humor_score DECIMAL(5,2),
    positive_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cleaned_review_id) REFERENCES cleaned_reviews(id)
);

CREATE TABLE IF NOT EXISTS morning_messages (
    id SERIAL PRIMARY KEY,
    scored_review_id INTEGER NOT NULL,
    message_date DATE UNIQUE NOT NULL,
    original_review TEXT NOT NULL,
    formatted_message TEXT NOT NULL,
    commentary TEXT,
    is_displayed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scored_review_id) REFERENCES scored_reviews(id)
);

CREATE TABLE IF NOT EXISTS filtered_reviews (
    id SERIAL PRIMARY KEY,
    cleaned_review_id INTEGER NOT NULL,
    filter_type VARCHAR(50) NOT NULL,
    is_passed BOOLEAN DEFAULT TRUE,
    filter_reason TEXT,
    filtered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cleaned_review_id) REFERENCES cleaned_reviews(id)
);

CREATE TABLE IF NOT EXISTS evening_messages (
    id SERIAL PRIMARY KEY,
    scored_review_id INTEGER NOT NULL,
    message_date DATE UNIQUE NOT NULL,
    original_review TEXT NOT NULL,
    formatted_message TEXT NOT NULL,
    commentary TEXT,
    is_displayed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scored_review_id) REFERENCES scored_reviews(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
