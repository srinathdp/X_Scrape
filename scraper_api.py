#!/usr/bin/env python3

import sys
import json
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load env variables
load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}
BASE_URL = "https://api.twitter.com/2"

def parse_date(date_str):
    """Parse date string into datetime object"""
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

def twitter_api_get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_tweets(query, max_results=10, next_token=None, start_time=None, end_time=None):
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,entities",
    }
    if next_token:
        params["next_token"] = next_token
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    return twitter_api_get("/tweets/search/recent", params)

def handle_search_tweets(params):
    """Handle search tweets request"""
    query = params.get("query", "")
    target_count = int(params.get("count", 30))
    if not query:
        return {"error": "Query is required"}

    tweets_fetched = 0
    tweets_list = []
    next_token = None

    while tweets_fetched < target_count:
        result = fetch_tweets(query, max_results=min(100, target_count-tweets_fetched), next_token=next_token)
        tweets = result.get("data", [])
        tweets_list.extend(tweets)
        tweets_fetched += len(tweets)
        next_token = result.get("meta", {}).get("next_token")
        if not next_token or not tweets:
            break

    return {
        "success": True,
        "tweets": tweets_list,
        "count": tweets_fetched
    }

def handle_hashtag_tweets(params):
    """Handle hashtag tweets request"""
    hashtag = params.get("hashtag", "")
    target_count = int(params.get("count", 30))
    if not hashtag:
        return {"error": "Hashtag is required"}
    query = f"#{hashtag}"
    return handle_search_tweets({"query": query, "count": target_count})

def handle_date_range_tweets(params):
    query = params.get("query", "")
    start_date_str = params.get("startDate")
    end_date_str = params.get("endDate")
    target_count = int(params.get("count", 30))
    if not query:
        return {"error": "Query is required"}
    if not start_date_str or not end_date_str:
        return {"error": "Start date and end date are required"}

    # Convert to RFC3339 timestamps if needed
    start_time = start_date_str
    end_time = end_date_str
    return handle_search_tweets({
        "query": query,
        "count": target_count,
        "start_time": start_time,
        "end_time": end_time
    })

def handle_user_tweets(params):
    screen_name = params.get("username", "")
    target_count = int(params.get("count", 30))
    if not screen_name:
        return {"error": "Username is required"}
    query = f"from:{screen_name}"
    return handle_search_tweets({"query": query, "count": target_count})

def main():
    """Main function to handle API requests"""
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Missing required arguments"}))
        return

    job_type = sys.argv[1]
    params_json = sys.argv[2]

    try:
        params = json.loads(params_json)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON parameters"}))
        return

    result = {"error": "Unknown job type"}
    if job_type == "SEARCH_TWEETS":
        result = handle_search_tweets(params)
    elif job_type == "HASHTAG_TWEETS":
        result = handle_hashtag_tweets(params)
    elif job_type == "DATE_RANGE_TWEETS":
        result = handle_date_range_tweets(params)
    elif job_type == "USER_TWEETS":
        result = handle_user_tweets(params)

    print(json.dumps(result))

if __name__ == "__main__":
    main()
