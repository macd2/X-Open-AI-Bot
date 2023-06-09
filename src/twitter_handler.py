import random
import time
from datetime import datetime, timedelta

import tweepy
from dotenv import dotenv_values

from config import config
from src.helper import df_from_tweepy_response, get_hash, filter_tweets_from_response
from src.communication_handler import logger
from src.pickle_handler import load_pickle, write_pickle




def create_api():
    env = dotenv_values(".env")
    consumer_key = env["consumer_key"]
    consumer_secret = env["consumer_secret"]
    access_token = env["access_token"]
    access_token_secret = env["access_token_secret"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    connector = tweepy.API(auth, wait_on_rate_limit=True)

    try:
        connector.verify_credentials()
    except Exception as e:
        logger.error("Error creating API", exc_info=True)
        raise e
    logger.info("API created")
    return connector


api_ = create_api()


def fetch_tweet(ids: list):
    ids = [str(i) for i in ids]
    return [x._json for x in api_.lookup_statuses(ids)]


def get_reply_to(mentions):
    in_reply_to_status_id = [x["in_reply_to_status_id_str"] for x in mentions]
    tweets = api_.lookup_statuses(in_reply_to_status_id)
    return [x._json for x in tweets]


def upload_image(image_path):
    return api_.media_upload(image_path)


def like_tweet(tweet_id):
    return api_.create_favorite(tweet_id)


def post_a_tweet(tweet: str):
    error = 200
    status = None
    try:
        status = api_.update_status(status=tweet)
    except Exception as e:
        error = e
    return status, error


def get_user_info(username):
    return api_.get_user(str(username))


def get_following_by_user(username):
    return api_.create_friendship(username)


def get_follower_by_username(username):
    user = get_user_info(username)
    return user.followers()


# function to perform data extraction
def get_tweet_by_hashtag(hashtag, since_days, num_tweets, return_df=False):
    date_since = datetime.today() - timedelta(days=since_days)
    date_since = date_since.strftime('%Y-%m-%d')  # format yyyy-mm--dd

    # We are using .Cursor() to search
    # through Twitter for the required tweets.
    # The number of tweets can be
    # restricted using .items(number of tweets)
    try:
        tweets = tweepy.Cursor(api_.search_tweets,
                               hashtag,
                               lang="en",
                               since_id=date_since,
                               tweet_mode='extended').items(num_tweets)
    except Exception as e:
        logger.error("Got error in twitter api_", e)
        logger.info("Retry")
        time.sleep(10)
        tweets = tweepy.Cursor(api_.search_tweets,
                               hashtag,
                               lang="en",
                               since_id=date_since,
                               tweet_mode='extended').items(num_tweets)

    if return_df:
        return df_from_tweepy_response(returned_status=tweets)
    else:
        return tweets


def reply_to_tweet(tweet, ai_response, like=True):
    if like:
        try:
            like_tweet(tweet_id=tweet["id"])
        except Exception as e:
            logger.error(e)

    error = 200
    status = None
    try:
        status = api_.update_status(f'{ai_response}', in_reply_to_status_id=int(tweet["id"]),
                                    auto_populate_reply_metadata=True)
    except Exception as e:
        error = e

    return status, error


def get_mentions(count=500):
    tweets = tweepy.Cursor(api_.mentions_timeline,
                           count=count,
                           tweet_mode='extended').items()
    # df = df_from_tweepy_response(returned_status=tweets)
    # d = df_to_dict(df)
    # t = []
    # for k, v in d.items():
    #     t.append(v)
    # return t
    list_tweets = [tweet for tweet in tweets]
    a = [tweet._json for tweet in list_tweets]
    for i in a:
        i["full_text_hash"] = get_hash(i["full_text"])
    return a


def get_tweets_and_filter(use_cached_tweets, hashtag):
    cached_filtered_tweets_file_name = "filtered_tweets"
    if use_cached_tweets:
        try:
            filtered_tweets = load_pickle(filename=cached_filtered_tweets_file_name, max_file_age_hrs=5)
            hashtag = filtered_tweets[0]["hashtag"]
            if filtered_tweets:
                return filtered_tweets, hashtag
        except Exception as e:
            logger.error(e)

    filtered_tweets = []
    # if no tweets found
    while not filtered_tweets:
        time.sleep(random.randrange(10, 20))
        tweepy_response = get_tweet_by_hashtag(hashtag=hashtag, since_days=3, num_tweets=500, return_df=False)
        filtered_tweets = filter_tweets_from_response(tweepy_response, min_text_len=70)
        if not filtered_tweets:
            logger.info(f"Found no Tweets for Hashtag: {hashtag}")
            hashtag = random.choice(config["hashtags"])
            logger.info(f"Try new Hashtag: {hashtag}")

    write_pickle(obj=filtered_tweets, filename=cached_filtered_tweets_file_name, hashtag=hashtag)

    return filtered_tweets, hashtag
