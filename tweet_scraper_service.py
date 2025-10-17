import os
import json
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Load environment variables
load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
API_URL = "https://api.twitter.com/2"
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

class TweetScraperService:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_user = os.getenv("DB_USER", "root")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = "xdb"

    def connect_to_db(self):
        try:
            connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            return connection
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return None

    def create_job(self, job_type, query, parameters=None):
        try:
            connection = self.connect_to_db()
            if connection is None:
                return None
            cursor = connection.cursor()
            params_json = json.dumps(parameters) if parameters else None
            query_sql = """
                INSERT INTO scraping_jobs
                (job_type, query, parameters, start_time, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(query_sql, (job_type, query, params_json, current_time, 'RUNNING'))
            job_id = cursor.lastrowid
            connection.commit()
            print(f"Created new scraping job with ID: {job_id}")
            return job_id
        except Error as e:
            print(f"Error creating job: {e}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def update_job_status(self, job_id, status, tweet_count=None):
        try:
            connection = self.connect_to_db()
            if connection is None:
                return
            cursor = connection.cursor()
            if status in ['COMPLETED', 'FAILED']:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                query = """
                    UPDATE scraping_jobs
                    SET status = %s, end_time = %s, tweet_count = %s
                    WHERE job_id = %s
                """
                cursor.execute(query, (status, current_time, tweet_count, job_id))
            else:
                query = "UPDATE scraping_jobs SET status = %s WHERE job_id = %s"
                cursor.execute(query, (status, job_id))
            connection.commit()
        except Error as e:
            print(f"Error updating job status: {e}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def save_tweets(self, job_id, tweets):
        try:
            connection = self.connect_to_db()
            if connection is None:
                return
            cursor = connection.cursor()
            tweets_saved = 0
            for tweet in tweets:
                hashtags = re.findall(r'#(\w+)', tweet.get('text', ''))
                user_info = tweet.get('author_id', None)
                tweet_data = {
                    'id': tweet.get('id'),
                    'text': tweet.get('text', ''),
                    'user_id': user_info,
                    'created_at': tweet.get('created_at', None),
                    'reply_count': tweet.get('public_metrics', {}).get('reply_count', 0),
                    'retweet_count': tweet.get('public_metrics', {}).get('retweet_count', 0),
                    'like_count': tweet.get('public_metrics', {}).get('like_count', 0),
                    'hashtags': hashtags,
                    'raw_data': tweet
                }

                query = """
                    INSERT INTO tweets
                    (id, job_id, user_id, text, created_at, reply_count, retweet_count,
                    like_count, hashtags, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    job_id = %s,
                    text = %s,
                    reply_count = %s,
                    retweet_count = %s,
                    like_count = %s,
                    hashtags = %s,
                    raw_data = %s
                """
                values = (
                    tweet_data['id'], job_id, tweet_data['user_id'], tweet_data['text'],
                    tweet_data['created_at'], tweet_data['reply_count'],
                    tweet_data['retweet_count'], tweet_data['like_count'],
                    json.dumps(hashtags), json.dumps(tweet_data['raw_data']),
                    # For ON DUPLICATE KEY UPDATE
                    job_id, tweet_data['text'], tweet_data['reply_count'],
                    tweet_data['retweet_count'], tweet_data['like_count'],
                    json.dumps(hashtags), json.dumps(tweet_data['raw_data'])
                )
                cursor.execute(query, values)
                tweets_saved += 1
            connection.commit()
            print(f"Saved {tweets_saved} tweets to database")
            return tweets_saved
        except Error as e:
            print(f"Error saving tweets: {e}")
            return 0
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def fetch_tweets(self, query, max_results=30, next_token=None, start_time=None, end_time=None):
        params = {
            'query': query,
            'max_results': min(100, max_results),
            'tweet.fields': 'created_at,public_metrics,entities,author_id'
        }
        if next_token:
            params['next_token'] = next_token
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        url = f"{API_URL}/tweets/search/recent"
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        return resp.json()

    def search_tweets(self, job_id, query, target_count=30, start_time=None, end_time=None):
        try:
            total_tweets = 0
            all_tweets = []
            next_token = None
            while total_tweets < target_count:
                result = self.fetch_tweets(
                    query,
                    max_results=min(100, target_count - total_tweets),
                    next_token=next_token,
                    start_time=start_time,
                    end_time=end_time
                )
                tweets = result.get('data', [])
                if not tweets:
                    break
                all_tweets.extend(tweets)
                total_tweets += len(tweets)
                next_token = result.get("meta", {}).get("next_token")
                if not next_token:
                    break
            self.save_tweets(job_id, all_tweets)
            self.update_job_status(job_id, 'COMPLETED', total_tweets)
            print(f"Final tweet count: {total_tweets}")
            return total_tweets
        except Exception as e:
            print(f"Error searching tweets: {e}")
            self.update_job_status(job_id, 'FAILED')
            return 0

    def search_hashtag_tweets(self, job_id, hashtag, target_count=30):
        query = f"#{hashtag.lstrip('#')}"
        return self.search_tweets(job_id, query, target_count=target_count)

    def search_date_range_tweets(self, job_id, query, start_date, end_date, target_count=30):
        start_iso = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_iso = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        return self.search_tweets(job_id, query, target_count=target_count, start_time=start_iso, end_time=end_iso)

    def search_user_tweets(self, job_id, username, target_count=30):
        query = f"from:{username}"
        return self.search_tweets(job_id, query, target_count=target_count)

# Example usage
if __name__ == "__main__":
    service = TweetScraperService()
    job_id = service.create_job(
        job_type="SEARCH_TWEETS",
        query="python",
        parameters={"target_count": 10}
    )
    if job_id:
        service.search_tweets(job_id, "python", 10)
