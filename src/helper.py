import datetime
import hashlib
import math
import re
from calendar import month_abbr
from collections import Counter
import inspect

# import pandas as pd

from src.communication_handler import logger


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


def replace_bad_hashtags(text: str):
    hashtag_mappings = {
        "#sarcasm": "#nooffense",
        "#grumpy": "",
        "#arrogant": "",
        "#sarcastic": "",
        "#motivation": "",
        "#skepticism": "",
    }

    for bad_hashtag, replacement in hashtag_mappings.items():
        text = text.replace(bad_hashtag, replacement)

    return text

def remove_content_between_markers(text, start_marker, end_marker):
    start_index = text.find(start_marker)
    end_index = text.find(end_marker)

    if start_index == -1 or end_index == -1:
        return text

    return text[:start_index] + text[end_index:]

def get_content_between_markers(text, start_marker, end_marker):
    startpos = text.find(start_marker) + len(start_marker)
    endpos = text.find(end_marker, startpos)
    return text[startpos:endpos].strip()

def filter_tweets_from_response(returned_status, min_text_len=70):
    tweets_to_consider = []

    for tweet in [tweet._json for tweet in returned_status]:
        full_text = tweet['full_text']
        if len(full_text) > min_text_len:
            tweet["symbols"] = [x for x in full_text if len(x) > 1 and "$" in x and not x[1].isdigit()]
            tweet['full_text_hash'] = get_hash(full_text)

            ffratio = tweet["user"].get('followers_count', 0) / max(tweet["user"].get('friends_count', 1), 1)
            tweet["ffratio"] = ffratio

            frt_ratio = tweet["user"].get('followers_count', 0) / max(tweet["user"].get('statuses_count', 1), 1)
            tweet["frt_ratio"] = frt_ratio

            # Filter Tweets
            c = full_text.lower()
            if (
                    tweet["ffratio"] < 1.2 and
                    tweet["frt_ratio"] > 0.023 and
                    tweet["user"].get('statuses_count', 0) > 100 and
                    tweet["user"].get('followers_count', 0) > 100 and
                    tweet['retweet_count'] < 200 and
                    len(full_text) > min_text_len and
                    "rt" not in c.split(" ") and
                    "follow" not in c.split(" ") and
                    "tag" not in c.split(" ") and
                    "airdrop" not in c.split(" ") and
                    "giveaway" not in c.split(" ") and
                    "binary" not in c.split(" ") and
                    "black woman" not in c and
                    "woman" not in c.split(" ")
            ):
                tweets_to_consider.append(tweet)

    return tweets_to_consider


# def df_from_tweepy_response(returned_status):
#     # takes a twitter courser object
#     # Creating DataFrame using pandas
#     # db = pd.DataFrame(columns=['username',
#     #                            "user_id",
#     #                            'description',
#     #                            'location',
#     #                            'following',
#     #                            'followers',
#     #                            'ffratio',  # followers / following
#     #                            'frt_ratio',  # followers / total-tweets
#     #                            'totaltweets',
#     #                            'retweetcount',
#     #                            'text',
#     #                            'cleanedtext',
#     #                            'hashtags',
#     #                            'symbols',
#     #                            'id'])
#
#     list_tweets = [tweet for tweet in returned_status]
#     a = [tweet._json for tweet in list_tweets]
#     d = pd.DataFrame(a)
#
#     # # Counter to maintain Tweet Count
#     # c = 1
#     #
#     # # we will iterate over each tweet in the
#     # # list for extracting information about each tweet
#     # for tweet in list_tweets:
#     #     username = tweet.user.screen_name
#     #     user_id = tweet.user.id
#     #     description = tweet.user.description
#     #     location = tweet.user.location
#     #     following = tweet.user.friends_count
#     #     followers = tweet.user.followers_count
#     #     totaltweets = tweet.user.statuses_count
#     #     retweetcount = tweet.retweet_count
#     #     hashtags = tweet.entities['hashtags']
#     #     id = tweet.id
#     #     # replied_tweet = tweet.replied_tweets
#     #
#     #     # Retweets can be distinguished by
#     #     # a retweeted_status attribute,
#     #     # in case it is an invalid reference,
#     #     # except block will be executed
#     #
#     #     try:
#     #         text = tweet.retweeted_status.full_text
#     #     except AttributeError:
#     #         text = tweet.full_text
#     #     hashtext = list()
#     #     for j in range(0, len(hashtags)):
#     #         hashtext.append(hashtags[j]['text'])
#     #
#     #     symbols = []
#     #     for x in text.split():
#     #         if len(x) > 1 and "$" in x and not x[1].isdigit():
#     #             symbols.append(x)
#     #
#     #     try:
#     #         ffratio = followers / following
#     #     except ZeroDivisionError:
#     #         ffratio = 0
#     #
#     #     try:
#     #         frt_ratio = followers / totaltweets
#     #     except ZeroDivisionError:
#     #         frt_ratio = 0
#     #
#     #     # Here we are appending all the
#     #     # extracted information in the DataFrame
#     #     ith_tweet = [username,
#     #                  user_id,
#     #                  description,
#     #                  location,
#     #                  following,
#     #                  followers,
#     #                  ffratio,
#     #                  frt_ratio,
#     #                  totaltweets,
#     #                  retweetcount,
#     #                  text,
#     #                  clean_tweet(text),
#     #                  hashtext,
#     #                  symbols,
#     #                  id]
#     #     db.loc[len(db)] = ith_tweet
#     #
#     #     # Function call to print tweet data on screen
#     #     # printtweetdata(i, ith_tweet)
#     #     c += 1
#     return d


def unified_logger_output(model_response=None, personality=None, nuance=None, mood=None, temp=None, model=None):
    log_message = ""
    if model_response:
        log_message += f"Model Response: {model_response}\n"
        log_message += f"Response Len: {len(model_response)}\n"
    if personality:
        log_message += f"Personality: {personality}\n"
    if nuance:
        log_message += f"Nuance: {nuance}\n"
    if mood:
        log_message += f"Mood: {mood}\n"
    if temp:
        log_message += f"Temp: {temp}\n"
    if model:
        log_message += f"Model: {model}\n"

    log_message += "-------------------------------"

    logger.info(log_message)

def whoami():
    frame = inspect.currentframe()
    return inspect.getframeinfo(frame).function
import sys
def callersname():
    return f"{sys._getframe(2).f_code.co_name}".upper()