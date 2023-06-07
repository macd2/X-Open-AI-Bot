import logging
import random
import time
from time import sleep

from src.abilities import reply_to_mentions, post_news_tweet, reply_to_tweet_by_hashtag
from src.sql_handler import init_db
from config import config
import datetime

from multiprocessing import Process
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

init_db()


# @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def reply_tweet():
    while True:
        temperature = random.choice(config["temps"])
        ai_personality = random.choice(config["ai_personalities"])
        mood = random.choice(config["moods"])
        nuance = random.choice(config["nuances"])
        like = random.choice(config["likes"])
        model = config["models"][0]

        hashtag = random.choice(config["hastags"])

        reply_to_tweet_by_hashtag(hashtag=hashtag, like=like, mood=mood, nuance=nuance, model=model,
                                  ai_personality=ai_personality, temperature=temperature, use_cahched_tweets=True, n_posts =5)

        sleep_time = random.randrange(1 * 60 * 60, 5 * 60 * 60)  # between 4 and 6 hours
        logger.info(f"---> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: Reply to tweets complete sleeping for minutes: {int(sleep_time / 60)}")
        sleep(sleep_time)


# @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def reply_mentions():
    while True:
        time.sleep(random.randrange(10, 50))
        model = config["models"][0]
        temperature = random.choice(config["temps"])
        ai_personality = "you are a funny guy always joking around and make humans laugh"
        mood = random.choice(config["moods"])
        nuance = random.choice(config["nuances"])
        like = random.choice(config["likes"])

        reply_to_mentions(like=like, mood=mood, nuance=nuance, ai_personality=ai_personality, temperature=temperature,
                          model=model)

        sleep_time = random.randrange(4 * 60 * 60, 6 * 60 * 60)
        logger.info(f'---> {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Reply mentions complete sleeping for minutes: {int(sleep_time / 60)}')
        sleep(sleep_time)


# @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def post_tweet():
    while True:
        model = config["models"][0]
        temperature = random.choice(config["temps"])
        ai_personality = random.choice(config["ai_personalities"])
        mood = random.choice(config["moods_news_post"])
        nuance = random.choice(config["nuances"])

        search_term = random.choice(config["search_terms"])

        post_news_tweet(search_term=search_term, mood=mood, nuance=nuance, ai_personality=ai_personality,
                        temperature=temperature, model=model)

        sleep_time = random.randrange(1 * 60 * 60, 3 * 60 * 60)
        logger.info(f"---> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}: Post new tweets complete sleeping for minutes: {int(sleep_time / 60)}")
        sleep(sleep_time)

#
# if __name__ == "__main__":
#     p1 = Process(target=post_tweet)
#     p1.start()
#     p2 = Process(target=reply_mentions)
#     p2.start()
#     p3 = Process(target=reply_tweet)
#     p3.start()
#     p1.join()
#     p2.join()
#     p3.join()

post_tweet()