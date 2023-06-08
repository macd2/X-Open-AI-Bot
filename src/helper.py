
import datetime
from calendar import month_abbr
import hashlib
import pandas as pd

import math
import re
from collections import Counter

from src.logger_handler import setup_logger

logger = setup_logger()
def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def text_to_vector(text):
    word = re.compile(r"\w+")
    words = word.findall(text)
    return Counter(words)


def get_cosine_similarity_score(text1, text2):
    """A score higher than 0.5 indicates a high similarity"""
    return get_cosine(text_to_vector(text1), text_to_vector(text2))


def find_hashtags(tweet):
    return re.findall("#([a-zA-Z0-9_]{1,50})", tweet)


def find_mentions(tweet):
    return re.findall("@([a-zA-Z0-9_]{1,50})", tweet)


def clean_links(text):
    return re.sub(r'http\S+', '', text)


def remove_hashtags(tweet):
    l = [x for x in tweet.split() if "#" not in x]
    return ' '.join(l)


# def remove_symbols(tweet):
#   l = [x for x in tweet.split() if "$" not in x and not x[1].isdigit()]
#   return ' '.join(l)

def remove_symbols(tweet):
    l = []
    for x in tweet.split():
        if len(x) > 1 and "$" not in x and not x[1].isdigit():
            l.append(x)
    return ' '.join(l)


def remove_mentions(tweet):
    l = [x for x in tweet.split() if "@" not in x]
    return ' '.join(l)


def clean_tweet(tweet):
    tweet = clean_links(tweet)
    tweet = remove_symbols(tweet)
    tweet = remove_hashtags(tweet)
    tweet = remove_mentions(tweet)
    return tweet


def df_to_dict(df):
    # drop na to avoid errors
    df.dropna(inplace=True)
    # converting to dict
    return df.to_dict(orient='index')


def filter_tweets(df):
    tweets_to_consider = []
    d = df_to_dict(df)
    for k, v in d.items():
        c = f'{v["text"]}'
        t = [
            v["ffratio"] < 1,
            v["totaltweets"] > 100,
            v["followers"] > 100,
            v["followers"] / v["totaltweets"] > 0.023,
            3 < v["retweetcount"] < 100,
            len(c) > 100,
            "rt" not in c.lower(),
            "follow" not in c.lower(),
            "tag" not in c.lower(),
            "airdrop" not in c.lower(),
            "giveaway" not in c.lower(),
        ]
        if sum(t) == len(t):
            tweets_to_consider.append(v)

    return tweets_to_consider

def convert_sec(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    # minutes = seconds // 60
    seconds %= 60
    return hour


def get_month_int_by_name(month):
    for k, v in enumerate(month_abbr):
        if v.lower() == month.lower():
            return k


def convert_tweepy_created_date_to_datetime(created_at):
    t2 = created_at.split(" ")
    t3 = f"{t2[-1]}-{get_month_int_by_name(t2[1])}-{t2[2]} {t2[3]}"
    # The format
    format_ = '%Y-%m-%d %H:%M:%S'
    datetime_str = datetime.datetime.strptime(t3, format_)
    return datetime_str


def get_hash(text):
    text = str(text)
    h = hashlib.new('sha256')  # sha256 can be replaced with different algorithms
    h.update(text.encode())  # give an encoded string.
    return h.hexdigest()


def replace_hashtags(text: str):

    text = text.replace("#sarcasm", "#nooffense")
    text = text.replace("#grumpy", "")
    text = text.replace("#arrogant", "")
    text = text.replace("#sarcastic", "")
    text = text.replace("#motivation", "")

    return text


def filter_tweets_from_response(returned_status, min_text_len=70):
    tweets_to_consider = []
    list_tweets = [tweet for tweet in returned_status]
    a = [tweet._json for tweet in list_tweets]
    for tweet in a:
        if len(tweet['full_text']) > min_text_len:

            tweet["symbols"] = [x for x in tweet["full_text"] if len(x) > 1 and "$" in x and not x[1].isdigit()]
            tweet['full_text_hash'] = get_hash(tweet["full_text"])
            try:
                ffratio = tweet["user"]['followers_count'] / tweet["user"]['friends_count']
            except ZeroDivisionError:
                ffratio = 0

            tweet["ffratio"] = ffratio
            try:
                frt_ratio = tweet["user"]['followers_count'] / tweet["user"]['statuses_count']
            except ZeroDivisionError:
                frt_ratio = 0
            tweet["frt_ratio"] = frt_ratio

            # Filter Tweets
            c = tweet['full_text']
            _ = [
                tweet["ffratio"] < 1.2,
                tweet["frt_ratio"] > 0.023,
                tweet["user"]['statuses_count'] > 100,
                tweet["user"]['followers_count'] > 100,
                tweet['retweet_count'] < 200,
                len(c) > min_text_len,
                "rt" not in c.lower().split(" "),
                "follow" not in c.lower().split(" "),
                "tag" not in c.lower().split(" "),
                "airdrop" not in c.lower().split(" "),
                "giveaway" not in c.lower().split(" "),
                "binary" not in c.lower().split(" ")
            ]
            if sum(_) == len(_):
                tweets_to_consider.append(tweet)

    return tweets_to_consider


def df_from_tweepy_response(returned_status):
    # takes a twitter courser object
    # Creating DataFrame using pandas
    # db = pd.DataFrame(columns=['username',
    #                            "user_id",
    #                            'description',
    #                            'location',
    #                            'following',
    #                            'followers',
    #                            'ffratio',  # followers / following
    #                            'frt_ratio',  # followers / total-tweets
    #                            'totaltweets',
    #                            'retweetcount',
    #                            'text',
    #                            'cleanedtext',
    #                            'hashtags',
    #                            'symbols',
    #                            'id'])

    list_tweets = [tweet for tweet in returned_status]
    a = [tweet._json for tweet in list_tweets]
    d = pd.DataFrame(a)

    # # Counter to maintain Tweet Count
    # c = 1
    #
    # # we will iterate over each tweet in the
    # # list for extracting information about each tweet
    # for tweet in list_tweets:
    #     username = tweet.user.screen_name
    #     user_id = tweet.user.id
    #     description = tweet.user.description
    #     location = tweet.user.location
    #     following = tweet.user.friends_count
    #     followers = tweet.user.followers_count
    #     totaltweets = tweet.user.statuses_count
    #     retweetcount = tweet.retweet_count
    #     hashtags = tweet.entities['hashtags']
    #     id = tweet.id
    #     # replied_tweet = tweet.replied_tweets
    #
    #     # Retweets can be distinguished by
    #     # a retweeted_status attribute,
    #     # in case it is an invalid reference,
    #     # except block will be executed
    #
    #     try:
    #         text = tweet.retweeted_status.full_text
    #     except AttributeError:
    #         text = tweet.full_text
    #     hashtext = list()
    #     for j in range(0, len(hashtags)):
    #         hashtext.append(hashtags[j]['text'])
    #
    #     symbols = []
    #     for x in text.split():
    #         if len(x) > 1 and "$" in x and not x[1].isdigit():
    #             symbols.append(x)
    #
    #     try:
    #         ffratio = followers / following
    #     except ZeroDivisionError:
    #         ffratio = 0
    #
    #     try:
    #         frt_ratio = followers / totaltweets
    #     except ZeroDivisionError:
    #         frt_ratio = 0
    #
    #     # Here we are appending all the
    #     # extracted information in the DataFrame
    #     ith_tweet = [username,
    #                  user_id,
    #                  description,
    #                  location,
    #                  following,
    #                  followers,
    #                  ffratio,
    #                  frt_ratio,
    #                  totaltweets,
    #                  retweetcount,
    #                  text,
    #                  clean_tweet(text),
    #                  hashtext,
    #                  symbols,
    #                  id]
    #     db.loc[len(db)] = ith_tweet
    #
    #     # Function call to print tweet data on screen
    #     # printtweetdata(i, ith_tweet)
    #     c += 1
    return d


def unified_logger_output(model_response=None, personality=None, nuance=None, mood=None, temp=None, model=None):
    logger.info(f"Model Response: {model_response}")
    logger.info(f"Personality: {personality}")
    logger.info(f"Nuance: {nuance}")
    logger.info(f"Mood: {mood}")
    logger.info(f"Temp: {temp}")
    logger.info(f"Model: {model}")
    if model_response:
        logger.info(f"Response Len: {len(model_response)}")
    logger.info("-------------------------------")
