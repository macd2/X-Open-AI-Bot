import logging
import random
import time
from time import sleep

from src.helper import get_hash, replace_hashtags, get_cosine_simalarity_score, \
    unified_logger_output
from src.open_ai_handler import ask_gpt, tweak_gpt_outputs
from src.prompt_engineering import build_twitter_prompt, build_chat_log_conversation, build_twitter_prompt_for_news
from src.search_handler import return_news_list
from src.sql_handler import sql_check_text_already_replied, sql_write_replied_tweet_meta, \
    sql_mention_already_asnwered, \
    sql_write_mentions_meta, sql_news_already_posted, sql_write_timeline_posts, sql_get_n_latest_records
from src.twitter_handler import reply_to_tweet, get_mentions, post_a_tweet, get_tweets_and_filter

logger = logging.getLogger()


def reply_to_tweet_by_hashtag(hashtag, like, mood, nuance, ai_personality, model, temperature=0.8,
                              use_cahched_tweets=True, n_posts=1):
    logger.info(f"Filter tweets by hashtag: {hashtag}")

    filtered_tweets, hashtag = get_tweets_and_filter(use_cahched_tweets=use_cahched_tweets, hashtag=hashtag)

    if use_cahched_tweets and sql_check_text_already_replied(filtered_tweets[-1]["full_text_hash"]):
        # If the last element in the filtered tweet is already in the database this means we need to fetch new tweets
        filtered_tweets, hashtag = get_tweets_and_filter(use_cahched_tweets=False, hashtag=hashtag)

    logger.info(f"Got {len(filtered_tweets)} filtered tweets")
    logger.info("")
    c = 0
    for tweet in filtered_tweets:
        if sql_check_text_already_replied(tweet["full_text_hash"]):
            continue

        if "have questions" in tweet['full_text'].lower() or "have a questions" in tweet['full_text'].lower():
            mood = "with a an answer"
        prompt = build_twitter_prompt(mood=mood, question=tweet['full_text'], nuance=nuance)

        response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                           ability="reply_to_tweet_by_hashtag")

        # Post the reply
        while len(response) > 280:
            logger.info("Answer to long regenerate")
            response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                               ability="reply_to_tweet_by_hashtag")
            time.sleep(2)

        # Reply to the tweet
        logger.info("Sending Reply...")
        response = replace_hashtags(response)
        # ToDo implement a try except to catch Error in particular
        # tweepy.errors.Forbidden: 403 Forbidden
        # 433 - The original Tweet author restricted who can reply to this Tweet.

        status, error = reply_to_tweet(tweet=tweet, like=like, ai_response=response, image_path=None)
        if error:
            logger.info(f"Sending not Successful got error: {error}")
            t = {
                "hashtag": hashtag,
                "input_tweet": tweet['full_text'],
                "input_tweet_hash": tweet["full_text_hash"],
                "input_tweet_id": tweet["id"],
                "output_to_username": tweet["user"]['screen_name'],
                "output_tweet": response,
                "output_tweet_id": None,
                "status": str(error),
            }
            # Write the new reply to the db
            sql_write_replied_tweet_meta(tweet_data=t)
            continue

        else:
            # logg data
            unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
                                  temp=temperature, model=model)

            t = {
                "hashtag": hashtag,
                "input_tweet": tweet['full_text'],
                "input_tweet_hash": tweet["full_text_hash"],
                "input_tweet_id": tweet["id"],
                "output_to_username": tweet["user"]['screen_name'],
                "output_tweet": response,
                "output_tweet_id": status._json["id"],
                "status": str(error),
            }
            # Write the new reply to the db
            sql_write_replied_tweet_meta(tweet_data=t)
            c += 1
            if c == n_posts:
                break
            else:
                time.sleep(random.randrange(1, 5))


def reply_to_mentions(like, mood, nuance, ai_personality, temperature, model):
    logger.info("Replying to mentions")

    # Get the mentions
    mentions = get_mentions(count=500)
    logger.info(f"Found {len(mentions)} Tweets where I was mentioned")

    logger.info("Get previous answer...")

    # reply_to = get_reply_to(mentions)
    # logger.info("---------------------------")
    #
    # for i in mentions:
    #     for x in reply_to:
    #         if i["in_reply_to_status_id_str"] == x["id_str"]:
    #             i["replay_to_text"] = x["text"]

    for tweet in mentions:
        # Check if the mention has already been answered in the database
        if sql_mention_already_asnwered(tweet["id"]):
            logger.info(f"No action mention already replied to: {tweet['id']}\n")
            continue

        # Build the prompt for the model using the tweet text, mood, and nuance
        # prompt = build_twitter_prompt(question=tweet["full_text"], mood=mood, nuance=nuance)

        chat_log = build_chat_log_conversation(reply=tweet["full_text"], replied_to_text="",  # tweet["replay_to_text"],
                                               ai_personality=ai_personality)
        prompt = {"prompt": None, "nuance": None, "mood": None}

        # Get the response from the GPT model
        logger.info(f"Get Response from: {model}")

        response = ask_gpt(chat_log=chat_log, prompt=prompt, ai_personality=ai_personality, temperature=temperature,
                           model=model, ability="reply_to_mentions")
        # Make sure the response length is within Twitter's limit
        while len(response) > 280:
            logger.info(f"Response to long regenerating Len: {len(response)}")
            response = ask_gpt(chat_log=chat_log, prompt=prompt, ai_personality=ai_personality, temperature=temperature,
                               model=model, ability="reply_to_mentions")
            time.sleep(random.randrange(10, 20))

        response = tweak_gpt_outputs(gpt_response=response)
        logger.info(f"Reply to: {tweet['full_text']}")
        unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
                              temp=temperature, model=model)

        # import pickle
        # path = './test.pickle'
        # with open(path, 'rb') as handle:
        #     status = pickle.load(handle)

        # Reply to the tweet and get the status of the reply
        logger.info("Sending Reply to mention...")
        status, error = reply_to_tweet(tweet=tweet, ai_response=response, like=True)
        if error != 200:
            # when the poster replies anything else than 200 we encountered an error.
            logger.info(error)
            t = dict(in_reply_to_status_id=tweet["id"],
                     in_reply_to_text=tweet['full_text'],
                     in_reply_to_text_hash=tweet['full_text_hash'],
                     in_reply_to_user_name=tweet["user"]["screen_name"],
                     in_reply_to_user_id=tweet["user"]["id"],
                     replay_text=response,
                     replay_tweet_id=None,
                     status=str(error))

        else:
            t = dict(in_reply_to_status_id=tweet["id"],
                     in_reply_to_text=tweet['full_text'],
                     in_reply_to_text_hash=tweet['full_text_hash'],
                     in_reply_to_user_name=tweet["user"]["screen_name"],
                     in_reply_to_user_id=tweet["user"]["id"],
                     replay_text=response,
                     replay_tweet_id=status.id,
                     status=str(error))

        # Write the new reply data to the database
        sql_write_mentions_meta(mentions_data=t)
        sleep_time = 10
        logger.info(f"Waiting {sleep_time} seconds")
        sleep(sleep_time)


def post_news_tweet(search_term, mood, nuance, ai_personality, temperature, model, use_cache=True):
    logger.info(f"Use Search term: {search_term}")
    ddgs_news_gen, search_term = return_news_list(search_term=search_term, use_cache=True, use_api=True,
                                                  hrs_since_news=8)

    if use_cache and sql_news_already_posted(hash_=ddgs_news_gen[-1]["body_hash"], url=ddgs_news_gen[-1]["url"]):
        # If the last element in the search results is already in the database this means we need to fetch new results
        ddgs_news_gen, search_term = return_news_list(search_term=search_term, use_cache=False, use_api=True,
                                                      hrs_since_news=8)

    # make sure to post different content
    # there for we check for similarity in the posts
    last_ten_posts = [x[0] for x in sql_get_n_latest_records(table_name='timeline_posts', columne_name="body", n=10)]

    result_list = []
    while not result_list:
        for v in ddgs_news_gen:
            sublist = []
            for i in last_ten_posts:
                score = get_cosine_simalarity_score(text1=v["body"], text2=i)
                if score > 0.45:
                    sublist.append(False)
                else:
                    sublist.append(True)
            if all(sublist):
                result_list.append(v)
        if not result_list:
            ddgs_news_gen, search_term = return_news_list(search_term=search_term, use_cache=False, use_api=True,
                                                          hrs_since_news=8)
        else:
            ddgs_news_gen = result_list

    if type(ddgs_news_gen) == list:
        for v in ddgs_news_gen:
            body = v["body"]

            if sql_news_already_posted(get_hash(body), url=v["url"]):
                logger.info("No action news already posted")
                continue

            logger.info("")
            logger.info('News: ' + body)

            prompt = build_twitter_prompt_for_news(question=body, mood=mood, nuance=nuance)
            response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                               ability="post_news_tweet")

            while len(response) > 250:
                logger.info(f"Response to long regenerating Len: {len(response)}")
                response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                                   ability="post_news_tweet")
                time.sleep(random.randrange(1, 5))

            response = replace_hashtags(response)
            # Add the original url of the news
            tweet = f"{response} {v['url']}"

            unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
                                  temp=temperature, model=model)

            logger.info("Sending Post...")
            status, error = post_a_tweet(tweet)

            if error != 200:
                logger.info(f"Sending not successful got: {error}")
                post_data = {
                    "search_term": search_term,
                    "body": body,
                    "body_hash": v["body_hash"],
                    "input_text_url": v['url'],
                    "output_text": response,
                    "post_tweet_id": None,
                    "status": str(error)
                }
            else:
                logger.info(f"In response to: {body}")
                logger.info(f"Tweet: {tweet}")
                post_data = {
                    "search_term": search_term,
                    "body": body,
                    "body_hash": v["body_hash"],
                    "input_text_url": v['url'],
                    "output_text": response,
                    "post_tweet_id": status.id,
                    "status": str(error)
                }

            sql_write_timeline_posts(post_data=post_data)
            # We only want to answer one item at a time
            break
