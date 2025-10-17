import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from .env file (DB credentials/config)
load_dotenv()

def create_database():
    """Create the database and required tables for tweet scraping jobs."""

    # Read database connection parameters from environment
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')

    try:
        # Connect to MySQL server (no database selected yet)
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # 1. Create main database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS xdb")
            print("Database 'xdb' created or already exists")

            # 2. Switch to 'xdb' database
            cursor.execute("USE xdb")

            # 3. Create table for scraping jobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_jobs (
                    job_id INT AUTO_INCREMENT PRIMARY KEY,
                    job_type VARCHAR(50) NOT NULL,
                    query VARCHAR(255) NOT NULL,
                    parameters JSON,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    status VARCHAR(20) NOT NULL,
                    tweet_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Table 'scraping_jobs' created or already exists")

            # 4. Create table for tweets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweets (
                    id VARCHAR(255) PRIMARY KEY,       -- Tweet ID
                    job_id INT,                        -- FK to scraping_jobs
                    user_name VARCHAR(255),            -- User who posted tweet
                    user_id VARCHAR(255),              -- X user ID
                    text TEXT,                         -- Tweet text
                    created_at DATETIME,               -- When tweet was created
                    reply_count INT DEFAULT 0,
                    retweet_count INT DEFAULT 0,
                    bookmark_count INT DEFAULT 0,
                    hashtags JSON,                     -- List of hashtags (as JSON)
                    raw_data JSON,                     -- Full raw tweet JSON
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES scraping_jobs(job_id)
                )
            """)
            print("Table 'tweets' created or already exists")

            # 5. Create indexes for fast lookups (job_id, created_at)
            try:
                # Drop & create job_id index if already exists
                cursor.execute("""
                    SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE table_schema=DATABASE() AND table_name='tweets'
                    AND index_name='idx_tweets_job_id'
                """)
                if cursor.fetchone()[0]:
                    cursor.execute("DROP INDEX idx_tweets_job_id ON tweets")
                cursor.execute("CREATE INDEX idx_tweets_job_id ON tweets(job_id)")

                # Drop & create created_at index if already exists
                cursor.execute("""
                    SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE table_schema=DATABASE() AND table_name='tweets'
                    AND index_name='idx_tweets_created_at'
                """)
                if cursor.fetchone()[0]:
                    cursor.execute("DROP INDEX idx_tweets_created_at ON tweets")
                cursor.execute("CREATE INDEX idx_tweets_created_at ON tweets(created_at)")

                print("Indexes created successfully")
            except Error as e:
                print(f"Warning when creating indexes: {e}")

            print("Database initialization completed successfully!")

    except Error as e:
        print(f"Error: {e}")

    finally:
        # Always close cursor & connection to clean up
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    create_database()
