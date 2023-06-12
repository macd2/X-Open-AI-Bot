import random
import re
import time
from time import sleep

from src.communication_handler import logger
from src.helper import get_hash, replace_bad_hashtags, get_cosine_similarity_score, \
    unified_logger_output, clean_links, remove_content_between_markers, callersname
from src.open_ai_handler import ask_gpt, tweak_gpt_outputs
from src.prompt_engineering import build_twitter_prompt, build_twitter_prompt_news, \
    build_chat_log, build_twitter_promt_for_reply_mentions
from src.search_handler import return_news_list, returns_news_list_news_api
from src.sql_handler import sql_check_text_already_replied, sql_write_replied_tweet_meta, \
    sql_mention_already_answered, \
    sql_write_mentions_meta, sql_news_already_posted, sql_write_timeline_posts, sql_get_n_latest_records
from src.twitter_handler import reply_to_tweet, get_mentions, post_a_tweet, get_tweets_and_filter, \
    check_if_replied_to_mention_and_update_db


def reply_to_tweet_by_hashtag(hashtag, like, mood, nuance, ai_personality, model, temperature=0.8,
                              use_cached_tweets=True, n_posts=1):
    logger.info(f"Filter tweets by hashtag: {hashtag}")

    filtered_tweets, hashtag = get_tweets_and_filter(use_cached_tweets=use_cached_tweets, hashtag=hashtag)

    if use_cached_tweets and sql_check_text_already_replied(filtered_tweets[-1]["full_text_hash"]):
        # If the last element in the filtered tweet is already in the database, fetch new tweets
        filtered_tweets, hashtag = get_tweets_and_filter(use_cached_tweets=False, hashtag=hashtag)

    logger.info(f"Got {len(filtered_tweets)} filtered tweets")
    logger.info("")
    c = 0
    for tweet in filtered_tweets:
        logger.info(f"Reply to Tweet by Hashtag {c}/{n_posts}")
        if sql_check_text_already_replied(tweet["full_text_hash"]):
            continue

        if "have questions" in tweet['full_text'].lower() or "have a question" in tweet['full_text'].lower():
            mood = "with an answer"
        prompt = build_twitter_prompt(mood=mood, question=tweet['full_text'], nuance=nuance)

        response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                           ability="reply_to_tweet_by_hashtag")

        # Post the reply
        while len(response) > 280:
            logger.info(f"reply_to_tweet_by_hashtag: Answer too long, regenerate Len: {len(response)}")
            response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                               ability="reply_to_tweet_by_hashtag")
            time.sleep(2)

        # Reply to the tweet
        raw_response = response
        response = replace_bad_hashtags(response)
        unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
                              temp=temperature, model=model)

        logger.info("Sending Reply...")
        status, error = reply_to_tweet(tweet=tweet, like=like, ai_response=response)

        if error != 200:
            logger.error(f"{callersname()} :Sending not Successful, Got error: {error}")

        t = {
            "hashtag": hashtag,
            "input_tweet": tweet['full_text'],
            "input_tweet_hash": tweet["full_text_hash"],
            "input_tweet_id": tweet["id"],
            "output_to_username": tweet["user"]['screen_name'],
            "output_tweet": response,
            "raw_model_response": raw_response,
            "output_tweet_id": None if error != 200 else status.id,
            "status": str(error),
        }
        # Write the new reply to the database
        sql_write_replied_tweet_meta(tweet_data=t)
        c += 1
        if c == n_posts:
            break
        else:
            time.sleep(random.randrange(1, 5))


def reply_to_mentions(like, mood, nuance, ai_personality, temperature, model):
    # Todo add more context get previouse replies and add to the conversation
    logger.info("Replying to mentions")

    # Get the mentions
    mentions = get_mentions(count=500)
    c = len(mentions)
    logger.info(f"Found {c} Tweets where I was mentioned")

    cc = 1

    # Updating the DB with already replied mentions to make sure no double answering happens even if there is an issue with the DB
    check_if_replied_to_mention_and_update_db(mentions=mentions, delete_multi_replies=True)

    for tweet in mentions:
        logger.info(f"Reply to mention {cc}/{c}")
        # Check if the mention has already been answered in the database
        if sql_mention_already_answered(tweet['id']):
            logger.info(f"No action! Already replied to Mention: {tweet['id']}\n")
            cc += 1
            continue
        # Make sure the reply contains text
        no_links = clean_links(tweet['full_text'])
        no_links = re.sub(r'(@)\S+', '', no_links)
        no_links = re.sub(r'\s+', ' ', no_links)

        if no_links.strip():
            # Build the prompt for the model using the tweet text, mood, and nuance
            # prompt = build_twitter_prompt(mood=mood, question=tweet['full_text'], nuance=nuance)
            prompt = build_twitter_promt_for_reply_mentions(mood=mood, question=tweet['full_text'], nuance=nuance)
            chat_log = build_chat_log(prompt=prompt["prompt"], ai_personality=ai_personality, replace_at_sings=True)

            # Get the response from the GPT model
            logger.info(f"Get Response from: {model}")
            response = ask_gpt(chat_log=chat_log, prompt=prompt, ai_personality=ai_personality, temperature=temperature,
                               model=model, ability="reply_to_mentions")
            # Make sure the response length is within Twitter's limit
            while len(response) > 280:
                logger.info(f"Reply to mention: Response too long! Regenerating Len: {len(response)}")
                response = ask_gpt(chat_log=chat_log, prompt=prompt, ai_personality=ai_personality,
                                   temperature=temperature,
                                   model=model, ability="reply_to_mentions")
                time.sleep(random.randrange(10, 20))

            response = remove_content_between_markers(text=response, start_marker="It's important", end_marker="#")
            response = tweak_gpt_outputs(gpt_response=response)
            logger.info(f"Reply to: {tweet['full_text']}")
            unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
                                  temp=temperature, model=model)

            # Reply to the tweet and get the status of the reply
            logger.info(f"Sending Reply to mention {cc}/{c}")
            status, error = reply_to_tweet(tweet=tweet, ai_response=response, like=like)
        else:
            logger.info(f"No Text in reply skipping")
            error = "no text"
            response = None

        t = {
            "in_reply_to_status_id": tweet["id"],
            "in_reply_to_text": tweet['full_text'],
            "in_reply_to_text_hash": tweet['full_text_hash'],
            "in_reply_to_user_name": tweet["user"]["screen_name"],
            "in_reply_to_user_id": tweet["user"]["id"],
            "replay_text": response,
            "replay_tweet_id": None if error != 200 else status.id,
            "status": str(error)
        }

        # Write the new reply data to the database
        sql_write_mentions_meta(mentions_data=t)
        sleep_time = random.randrange(10, 50)
        cc += 1
        logger.info(f"Waiting {sleep_time} seconds")
        sleep(sleep_time)


def post_news_tweet(search_term, mood, nuance, ai_personality, temperature, model, use_cache=True, randomize=True):
    logger.info(f"Use Search term: {search_term}")

    news_api_news, search_term = returns_news_list_news_api(search_term=search_term, use_cache=use_cache, use_api=True,
                                                            hrs_since_news=8)
    if not news_api_news:
        # This only happens when the api limit is reached
        return
    last_ten_posts = [x[0] for x in sql_get_n_latest_records(table_name='timeline_posts', column_name="body", n=10)]

    result_list = [v for v in news_api_news if
                   all(get_cosine_similarity_score(text1=v["body"], text2=i) <= 0.45 for i in last_ten_posts)]

    if not result_list:
        news_api_news, search_term = return_news_list(search_term=search_term, use_cache=False, use_api=True,
                                                      hrs_since_news=8)
        result_list = [v for v in news_api_news if
                       all(get_cosine_similarity_score(text1=v["body"], text2=i) <= 0.45 for i in last_ten_posts)]

    if result_list:
        for v in result_list:
            if randomize:
                v = random.choice(result_list)

            body = v["body"]

            if sql_news_already_posted(get_hash(v["description"]), url=v["url"]):
                logger.info("No action news already posted")
                continue

            logger.info('News: ' + body)

            prompt = build_twitter_prompt_news(question=body, mood=mood, nuance=nuance)
            response = []

            while len(response) > 260 or not response:
                if response:
                    logger.info(f"Response too long. Regenerating. Len: {len(response)}")
                response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
                                   ability="post_news_tweet")
                response = replace_bad_hashtags(response)
                time.sleep(random.randrange(1, 5))

            tweet = f"{response} {v['url']}"
            unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
                                  temp=temperature, model=model)

            logger.info("Sending Post...")
            status, error = post_a_tweet(tweet)

            if error != 200:
                logger.error(f"Sending not successful. Got: {error}")
            else:
                logger.info(f"In response to: {body}")
                logger.info(f"Tweet: {tweet}")

            post_data = {
                "search_term": search_term,
                "body": body,
                "news_date": v["publishedAt"],
                "description_hash": v["description_hash"],
                "input_text_url": v['url'],
                "output_text": response,
                "post_tweet_id": None if error != 200 else status.id,
                "status": str(error)
            }
            sql_write_timeline_posts(post_data=post_data)
            break
#
# def post_news_tweet(search_term, mood, nuance, ai_personality, temperature, model, use_cache=True):
#     logger.info(f"Use Search term: {search_term}")
#
#     ddgs_news_gen, search_term = return_news_list(search_term=search_term, use_cache=use_cache, use_api=True,
#                                                   hrs_since_news=8)
#     if not ddgs_news_gen:
#         # This only happens when the api limit is reached
#         return
#     last_ten_posts = [x[0] for x in sql_get_n_latest_records(table_name='timeline_posts', column_name="body", n=10)]
#
#     result_list = [v for v in ddgs_news_gen if
#                    all(get_cosine_similarity_score(text1=v["body"], text2=i) <= 0.45 for i in last_ten_posts)]
#
#     if not result_list:
#         ddgs_news_gen, search_term = return_news_list(search_term=search_term, use_cache=False, use_api=True,
#                                                   hrs_since_news=8)
#         result_list = [v for v in ddgs_news_gen if
#                    all(get_cosine_similarity_score(text1=v["body"], text2=i) <= 0.45 for i in last_ten_posts)]
#
#     if result_list:
#         for v in result_list:
#             body = v["body"]
#
#             if sql_news_already_posted(get_hash(body), url=v["url"]):
#                 logger.info("No action news already posted")
#                 continue
#
#             logger.info('News: ' + body)
#
#             prompt = build_twitter_prompt_news(question=body, mood=mood, nuance=nuance)
#             response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
#                                ability="post_news_tweet")
#
#             while len(response) > 250:
#                 logger.info(f"Response too long. Regenerating. Len: {len(response)}")
#                 response = ask_gpt(prompt=prompt, ai_personality=ai_personality, temperature=temperature, model=model,
#                                    ability="post_news_tweet")
#                 time.sleep(random.randrange(1, 5))
#
#             response = replace_bad_hashtags(response)
#             tweet = f"{response} {v['url']}"
#
#             unified_logger_output(model_response=response, personality=ai_personality, nuance=nuance, mood=mood,
#                                   temp=temperature, model=model)
#
#             logger.info("Sending Post...")
#             status, error = post_a_tweet(tweet)
#
#             if error != 200:
#                 logger.error(f"Sending not successful. Got: {error}")
#             else:
#                 logger.info(f"In response to: {body}")
#                 logger.info(f"Tweet: {tweet}")
#
#             post_data = {
#                 "search_term": search_term,
#                 "body": body,
#                 "body_hash": v["body_hash"],
#                 "input_text_url": v['url'],
#                 "output_text": response,
#                 "post_tweet_id": None if error != 200 else status.id,
#                 "status": str(error)
#             }
#             sql_write_timeline_posts(post_data=post_data)
#             break
