import datetime
import hashlib
import math
import re
import sys
from calendar import month_abbr
from collections import Counter

from src.communication_handler import logger


def clean_model_output(gpt_response):
    keywords = ["respectfully ", "It is important to ", "Possible response:", "I appreciate your response, but ",
                "@_RussellEdwards", "I have to respectfully disagree with the text between the * signs.",
                "Thanks for sharing", "Appreciate the share!", "Thanks for sharing!"]
    for i in keywords:
        if i.lower() in gpt_response.lower():
            logger.info(f"Replaced: {i}")
            gpt_response = gpt_response.lower().replace(i.lower(), "")
    return gpt_response


def model_not_comply_filter(answer):
    if "I'm sorry" in answer and "AI" in answer and "I cannot".lower() in answer.lower():
        logger.info("Model don't want to comply filter activated: I'm sorry, AI and I cannot in response")
        return True
    else:
        return False


def general_model_response_filter(filters, answer):
    for x in filters:
        if x.lower() in answer.lower():
            logger.info(f"General Repose filter activate on: {x}")
            return True
    return False


def find_hashtags(tweet):
    return re.findall("#([a-zA-Z0-9_]{1,50})", tweet)


def remove_hashtags(tweet):
    l = [x for x in tweet.split() if "#" not in x]
    return ' '.join(l)


def find_mentions(tweet):
    return re.findall("@([a-zA-Z0-9_]{1,50})", tweet)


def remove_mentions_with_at_sign(text):
    """Clean all @ signs before feeding to the model"""
    text = re.sub(r'(@)\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def clean_links(text):
    return re.sub(r'http\S+', '', text)


def remove_symbols(tweet):
    l = []
    for x in tweet.split():
        if len(x) > 1 and "$" not in x and not x[1].isdigit():
            l.append(x)
    return ' '.join(l)


def clean_tweet(tweet):
    tweet = clean_links(tweet)
    tweet = remove_symbols(tweet)
    tweet = remove_hashtags(tweet)
    tweet = remove_mentions_with_at_sign(tweet)
    return tweet


def get_text_hastag_ratio(text):
    i = clean_links(' '.join(text.split()))
    i = remove_mentions_with_at_sign(i)
    i = remove_symbols(i)

    b = " ".join(find_hashtags(i))
    if len(b) == 0:
        return 1
    a = remove_hashtags(i)
    if len(a) == 0:
        return False

    return (len(a.split(" ")) / len(b.split(" "))) / 10


def check_text_hastag_ratio(text):
    # accatable ratio is 0.5 and above
    a = get_text_hastag_ratio(text=text)
    if a and a > 0.5:
        return True
    else:
        return False

def replace_bad_hashtags(text: str):
    hashtag_mappings = {
        "#sarcasm": "#nooffense",
        "#grumpy": "",
        "#arrogant": "",
        "#sarcastic": "",
        "#motivation": "",
        "#skepticism": "",
        "#toxicmasculinity": "",
        "skeptical": "",
        "sceptical": "",
        "patience": "",
        "@_RussellEdwards": ""
    }

    for bad_hashtag, replacement in hashtag_mappings.items():
        text = text.lower().replace(bad_hashtag.lower(), replacement)
    return text


def replace_longest_hashtag(string, replacement=""):
    hashtag_words = [word for word in string.replace("#", " #").split() if word.startswith('#')]
    if not hashtag_words:
        return string

    longest_word = max(hashtag_words, key=len)
    replaced_string = string.replace(longest_word, replacement)
    return " ".join(replaced_string.split())


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


def get_hash(text):
    text = str(text)
    h = hashlib.new('sha256')  # sha256 can be replaced with different algorithms
    h.update(text.encode())  # give an encoded string.
    return h.hexdigest()


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
def get_date_for_days_delata_from_today(days_delta):
    date_since = datetime.today() - datetime.timedelta(days=days_delta)
    date_since = date_since.strftime('%Y-%m-%d')
    return date_since

def convert_tweepy_created_date_to_datetime(created_at):
    t2 = created_at.split(" ")
    t3 = f"{t2[-1]}-{get_month_int_by_name(t2[1])}-{t2[2]} {t2[3]}"
    # The format
    format_ = '%Y-%m-%d %H:%M:%S'
    datetime_str = datetime.datetime.strptime(t3, format_)
    return datetime_str


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


def callersname():
    return f"{sys._getframe(2).f_code.co_name}".upper()


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
