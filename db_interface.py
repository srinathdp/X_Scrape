#!/usr/bin/env python3

import sys
import json
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables for DB credentials
load_dotenv()

def connect_to_db():
    """Connect to the MySQL database using .env credentials."""
    try:
        host = os.getenv('DB_HOST', 'localhost')
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', 'root')
        db_name = 'xdb'
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        return connection
    except Error as e:
        print(json.dumps({"error": f"Error connecting to MySQL database: {str(e)}"}))
        sys.exit(1)

def get_all_jobs():
    """Fetch all scraping jobs from the jobs table, parse fields for output."""
    try:
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)
        # Get all jobs ~ newest first
        query = """
        SELECT * FROM scraping_jobs
        ORDER BY job_id DESC
        """
        cursor.execute(query)
        jobs = cursor.fetchall()
        processed_jobs = []
        for job in jobs:
            # Parse parameters JSON -> dict
            if job['parameters'] and isinstance(job['parameters'], str):
                try:
                    job['parameters'] = json.loads(job['parameters'])
                except:
                    job['parameters'] = {}
            # Format date fields for output
            if job['start_time']:
                job['start_time'] = job['start_time'].isoformat()
            if job['end_time']:
                job['end_time'] = job['end_time'].isoformat()
            if job['created_at']:
                job['created_at'] = job['created_at'].isoformat()
            processed_jobs.append(job)
        return {"success": True, "jobs": processed_jobs}
    except Error as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def get_job_with_tweets(params):
    """Fetch a specific job and all associated tweets by job_id."""
    try:
        job_id = params.get('jobId')
        if not job_id:
            return {"error": "Job ID is required"}
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)
        # Fetch job details by job_id
        job_query = """
        SELECT * FROM scraping_jobs
        WHERE job_id = %s
        """
        cursor.execute(job_query, (job_id,))
        job = cursor.fetchone()
        if not job:
            return {"error": "Job not found"}
        # Parse parameters JSON -> dict
        if job['parameters'] and isinstance(job['parameters'], str):
            try:
                job['parameters'] = json.loads(job['parameters'])
            except:
                job['parameters'] = {}
        # Format date fields for output
        if job['start_time']:
            job['start_time'] = job['start_time'].isoformat()
        if job['end_time']:
            job['end_time'] = job['end_time'].isoformat()
        if job['created_at']:
            job['created_at'] = job['created_at'].isoformat()
        # Fetch tweets for this job
        tweets_query = """
        SELECT * FROM tweets
        WHERE job_id = %s
        ORDER BY created_at DESC
        """
        cursor.execute(tweets_query, (job_id,))
        tweets = cursor.fetchall()
        processed_tweets = []
        for tweet in tweets:
            # Parse hashtags JSON -> list
            if tweet['hashtags'] and isinstance(tweet['hashtags'], str):
                try:
                    tweet['hashtags'] = json.loads(tweet['hashtags'])
                except:
                    tweet['hashtags'] = []
            # Parse raw_data JSON -> dict
            if tweet['raw_data'] and isinstance(tweet['raw_data'], str):
                try:
                    tweet['raw_data'] = json.loads(tweet['raw_data'])
                except:
                    tweet['raw_data'] = {}
            # Format date fields for output
            if tweet['created_at']:
                tweet['created_at'] = tweet['created_at'].isoformat()
            if tweet['indexed_at']:
                tweet['indexed_at'] = tweet['indexed_at'].isoformat()
            processed_tweets.append(tweet)
        return {
            "success": True,
            "job": job,
            "tweets": processed_tweets
        }
    except Error as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    """Main function: handles database queries from command line."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Operation is required"}))
        return
    operation = sys.argv[1]
    # Get additional parameters from input if provided
    params = {}
    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON parameters"}))
            return
    # Supported database query operations
    result = {"error": "Unknown operation"}
    if operation == "get_all_jobs":
        result = get_all_jobs()
    elif operation == "get_job_with_tweets":
        result = get_job_with_tweets(params)
    # Print result as JSON for output to consuming process/UI
    print(json.dumps(result))

if __name__ == "__main__":
    main()
