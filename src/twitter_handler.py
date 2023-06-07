import logging
import random
import time
from datetime import datetime, timedelta

import tweepy
from dotenv import dotenv_values

from config import config
from src.helper import df_from_tweepy_response, get_hash, filter_tweets_from_response
from src.pickle_handler import laod_pickle, write_pickle

logger = logging.getLogger()


def create_api():
    env = dotenv_values(".env")
    consumer_key = env["consumer_key"]
    consumer_secret = env["consumer_secret"]
    access_token = env["access_token"]
    access_token_secret = env["access_token_secret"]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    try:
        api.verify_credentials()
    except Exception as e:
        logger.error("Error creating API", exc_info=True)
        raise e
    logger.info("API created")
    return api


api = create_api()


def fetch_tweet(ids: list):
    ids = [str(i) for i in ids]
    return [x._json for x in api.lookup_statuses(ids)]


def get_reply_to(mentions):
    in_reply_to_status_id = [x["in_reply_to_status_id_str"] for x in mentions]
    tweets = api.lookup_statuses(in_reply_to_status_id)
    return [x._json for x in tweets]


def upload_image(image_path):
    return api.media_upload(image_path)


def like_tweet(tweet_id):
    return api.create_favorite(tweet_id)


def post_a_tweet(tweet):
    error = 200
    status = None
    try:
        status = api.update_status(status=str(tweet))
    except Exception as e:
        error = e
    return status, error


def get_user_info(usernname):
    return api.get_user(str(usernname))


def get_following_by_user(username):
    return api.create_friendship(username)


def get_follower_by_username(usernname):
    user = get_user_info(usernname)
    return user.followers()


# function to perform data extraction
def get_tweet_by_hashtag(hashtag, since_days, numtweet, return_df=False):
    date_since = datetime.today() - timedelta(days=since_days)
    date_since = date_since.strftime('%Y-%m-%d')  # format yyyy-mm--dd

    # We are using .Cursor() to search
    # through twitter for the required tweets.
    # The number of tweets can be
    # restricted using .items(number of tweets)
    try:
        tweets = tweepy.Cursor(api.search_tweets,
                               hashtag,
                               lang="en",
                               since_id=date_since,
                               tweet_mode='extended').items(numtweet)
    except Exception as e:
        logger.error("Got error in twitter api", e)
        logger.info("Retry")
        time.sleep(10)
        tweets = tweepy.Cursor(api.search_tweets,
                               hashtag,
                               lang="en",
                               since_id=date_since,
                               tweet_mode='extended').items(numtweet)

    if return_df:
        return df_from_tweepy_response(returned_status=tweets)
    else:
        return tweets


#    filename = 'get_tweet_by_hastagd_tweets.csv'
#    # we will save our database as a CSV file.
#    db.to_csv(filename)

# def get_filtered_tweets(hashtag, days_since, numtweet):
#     df = get_tweet_by_hashtag(hashtag, days_since, numtweet)
#     return filter_tweets(df)

# def reply_to_tweet(tweet, ai_response, like=True, image_path=None):
#     if like:
#         like_tweet(tweet_id=tweet["id"])
#     if image_path:
#         media = upload_image(image_path)
#         try:
#             result = api.update_status(f'{ai_response}', in_reply_to_status_id=int(tweet["id"]),
#                                        media_ids=[media.media_id], auto_populate_reply_metadata=True)
#         except Exception as e:
#             result = e
#
#     return api.update_status(f'{ai_response}', in_reply_to_status_id=int(tweet["id"]),
#                              auto_populate_reply_metadata=True)


def reply_to_tweet(tweet, ai_response, like=True, image_path=None):
    if like:
        try:
            like_tweet(tweet_id=tweet["id"])
        except Exception as e:
            pass

    error = 200
    status = None
    try:
        status = api.update_status(f'{ai_response}', in_reply_to_status_id=int(tweet["id"]),
                                   auto_populate_reply_metadata=True)
    except Exception as e:
        error = e

    return status, error


def get_mentions(count=500):
    tweets = tweepy.Cursor(api.mentions_timeline,
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


def get_tweets_and_filter(use_cahched_tweets, hashtag):
    cached_filtered_tweets_file_name = "filtered_tweets"
    if use_cahched_tweets:
        try:
            filtered_tweets = laod_pickle(filename=cached_filtered_tweets_file_name, max_file_age_hrs=5)
            hashtag = filtered_tweets[0]["hashtag"]
            if filtered_tweets:
                return filtered_tweets, hashtag
        except Exception as e:
            pass

    filtered_tweets = []
    # if no tweets found
    while not filtered_tweets:
        time.sleep(random.randrange(10, 20))
        tweepy_response = get_tweet_by_hashtag(hashtag=hashtag, since_days=3, numtweet=500, return_df=False)
        filtered_tweets = filter_tweets_from_response(tweepy_response, min_text_len=70)
        if not filtered_tweets:
            logging.info(f"Found no Tweets for Hashtag: {hashtag}")
            hashtag = random.choice(config["hastags"])
            logging.info(f"Try new Hashtag: {hashtag}")

    write_pickle(obj=filtered_tweets, filename=cached_filtered_tweets_file_name, hashtag=hashtag)

    return filtered_tweets, hashtag
