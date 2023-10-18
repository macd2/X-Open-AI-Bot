import random
import time
from datetime import datetime, timedelta

import tweepy
from dotenv import dotenv_values

from config import config
from src.communication_handler import logger
from src.helper import callersname, clean_links, clean_twee_before_potst, filter_tweets_from_response, get_hash
from src.pickle_handler import load_pickle, write_pickle
from src.sql_handler import sql_already_in_db, sql_write_mentions_meta


def create_api():
    connected = False
    while not connected:
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
            # logger.error("Error creating API", exc_info=True)
            logger.error(f"Couldn't connect to twitter API got: {e}")
            logger.info("Retry")
            time.sleep(5)
            continue
        logger.info("Twitter API created")
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
        status = api_.update_status(status=clean_twee_before_potst(tweet))
    except tweepy.errors.TweepyException as e:
        logger.error(f"{callersname()}: Got error: {e}")
        error = e
    return status, error


def get_user_info(username):
    return api_.get_user(str(username))


def get_following_by_user(username):
    return api_.create_friendship(username)


def get_follower_by_username(username):
    user = get_user_info(username)
    return user.followers()


def delete_tweet(tweet_id):
    logger.info(f"Deleting tweet: {tweet_id}")
    # Delete the duplicate tweets
    try:
        api_.destroy_status(tweet_id)
    except tweepy.TweepyException as e:
        logger.error(f"Could not fetch user_timeline: {e}")


# def get_liked_tweets():
#     tweets = api_.get_favorites(id=id, tweet_fields=['context_annotations', 'created_at', 'geo'])
#
#     for tweet in tweets.data:
#         print(tweet)
# function to perform data extraction

def get_tweet_by_hashtag(hashtag: str, num_tweets=10):
     # format yyyy-mm--dd

    # We are using .Cursor() to search
    # through Twitter for the required tweets.
    # The number of tweets can be
    # restricted using .items(number of tweets)
    hashtag = hashtag.replace("#", "")
    #example queries
    # QUERY = "#javascript AND #backend -filter:retweets"
    #Example fo full text searxch
    # QUERY = "bitcoin OR python"
    #Example of searching for a mention and a hastag in the same tweet
    # QUERY = "@name AND #hastag"
    #Example To User and From User
    # QUERY = "from:user to:user"
    #Example for Attitudes just add a :) for positive or :( for negative tweets

    QUERY = f"#{hashtag} -filter:retweets -filter:reply"
    logger.info(f"Get tweets for {QUERY}")

    try:
        tweets = tweepy.Cursor(api_.search_tweets,
                               QUERY,
                               # result_type="popular",
                               result_type="recent",
                               lang="en",
                               count=10,
                               # since_id=tweet_id,
                               tweet_mode='extended').items()
    except Exception as e:
        logger.error(f"{callersname()} :Got error: {e}")
        logger.info("Retry")
        pass
    # if return_df:
    #     return df_from_tweepy_response(returned_status=tweets)
    # else:
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
        tweepy_response = get_tweet_by_hashtag(hashtag=hashtag, num_tweets=500)
        filtered_tweets = filter_tweets_from_response(tweepy_response, min_text_len=70)
        if not filtered_tweets:
            logger.info(f"Found no Tweets for Hashtag: {hashtag}")
            hashtag = random.choice(config["keywords"])
            logger.info(f"Try new Hashtag: {hashtag}")

    write_pickle(obj=filtered_tweets, filename=cached_filtered_tweets_file_name, hashtag=hashtag)

    return filtered_tweets, hashtag


def check_if_replied_to_mention(tweet_id):
    try:
        tweets = api_.user_timeline(exclude_replies=False, tweet_mode='extended')
        reply_tweet = [tweet for tweet in tweets if
                       tweet.in_reply_to_status_id is not None and str(tweet.in_reply_to_status_id) == str(tweet_id)]
        if reply_tweet:
            return True
    except tweepy.TweepyException as e:
        logger.error(f"Error occurred while fetching tweets: {e}")
        return False
    return False


def check_if_replied_to_mention_and_update_db(mentions, delete_multi_replies=True):
    logger.info(f"Checking if already replied ")
    try:
        tweets = api_.user_timeline(exclude_replies=False, tweet_mode='extended')
    except tweepy.TweepyException as e:
        logger.error(f"Could not fetch user_timeline: {e}")
        return

    for mention in mentions:
        status = 200
        reply_tweet = [tweet for tweet in tweets if
                       tweet.in_reply_to_status_id is not None and str(tweet.in_reply_to_status_id) == str(
                           mention["id"])]
        if len(reply_tweet) > 1:
            logger.info(f"Replied more than once to same tweet id: {reply_tweet[0].in_reply_to_status_id}")
            if delete_multi_replies:
                for i in reply_tweet[:-1]:
                    # when we are dealing with the Status object (in this case i is a Status object) we have to get values via status.key
                    delete_tweet(i.id)
                    time.sleep(random.randrange(1, 3))
                    status = "deleted"

        if reply_tweet:
            for tweet in reply_tweet:
                if not sql_already_in_db(table_name="mentions", columne="in_reply_to_text_hash",
                                         value=mention['full_text_hash']):
                    logger.info(f'Already Replayed to mention id: {mention["id"]} Updating DB')
                    t = dict(in_reply_to_status_id=mention["id"],
                             in_reply_to_text=mention['full_text'],
                             in_reply_to_text_hash=mention['full_text_hash'],
                             in_reply_to_user_name=mention["user"]["screen_name"],
                             in_reply_to_user_id=mention["user"]["id"],
                             replay_text=tweet.full_text,
                             replay_tweet_id=tweet.id,
                             status=str(status))
                    sql_write_mentions_meta(mentions_data=t)


class MyStreamingClient(tweepy.StreamingClient):
    def on_status(self, status):
        print("received tweet!")

    def on_tweet(self, tweet):
        if len(clean_links(tweet.text)) > 10:
            print(tweet)
            print("------------------")
        else:
            print("Tweet is short")

    def on_includes(self, includes):
        # print(includes)
        pass

    def on_error(self, status_code):
        print(status_code)
        if status_code == 420:
            return False

# env = dotenv_values(".env")
# bearer_token = env["bearer_token"]
#
#
# # # @_RussellEdwards
# def delete_all_rules():
#     a = stream.get_rules().data
#     for i in a:
#         stream.delete_rules(i.id)
#
#
# stream = MyStreamingClient(bearer_token=bearer_token)
# delete_all_rules()
#
# stream.add_rules(tweepy.StreamRule(value="(#trump) (-is:retweet -is:reply)"), dry_run=False)
#
# print("active rules are", stream.get_rules().data)
# stream.filter(expansions=["author_id", "referenced_tweets.id", "in_reply_to_user_id", "entities.mentions.username"])
