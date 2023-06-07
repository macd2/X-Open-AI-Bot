import shutil
import sqlite3
from datetime import datetime

from dotenv import dotenv_values

env = dotenv_values(".env")
db = sqlite3.connect(f"./storage/{env['db_name']}.db", timeout=5, isolation_level=None)


def get_now():
    return datetime.now()


def get_now_formatted():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def return_str(i):
    return str(i)


def return_int(i):
    return int(i)


def return_float(i):
    return float(i)


def sql_get_n_latest_records(table_name, columne_name, n):
    _ = db.execute(f"SELECT {str(columne_name)} FROM {str(table_name)} order by date desc LIMIT {n};").fetchall()
    return [i for i in _]


def init_db(tables=None):
    """ At the Program start, we look for the sql updates """
    if not tables:
        tables = [
            {"name": "mentions",
             "fields": ["in_reply_to_status_id", "in_reply_to_text", "in_reply_to_text_hash", "replay_tweet_id",
                        "replay_text", "in_reply_to_user_name", "in_reply_to_user_id", "status"]},
            {"name": "replied_tweets",
             "fields": ["hashtag", "input_tweet", "input_tweet_hash", "input_tweet_id", "output_tweet",
                        "output_tweet_id", "output_to_username", "status"]},
            {"name": "ai_params",
             "fields": ["question", "prompt", "response", "personality", "nuance", "mood", "model", "temperature",
                        "ability"]},
            {"name": "timeline_posts",
             "fields": ["search_term", "body", "body_hash", "input_text_url", "output_text", "post_tweet_id", "status"]}
        ]
    for table in tables:
        db.execute(f"CREATE TABLE IF NOT EXISTS {table['name']} (date TEXT)")
        table_info = db.execute(f"pragma table_info({table['name']})")
        a = [o[1] for o in table_info]
        for field in table["fields"]:
            if field not in a:
                if "id" in field.split("_"):
                    type_ = "INTEGER DEFAULT 0"
                elif field == "temperature":
                    type_ = "FLOAT DEFAULT 0"
                else:
                    type_ = "TEXT"
                db.execute(f"ALTER TABLE {table['name']} ADD COLUMN {field} {type_}")


def _build_write_sql_query(dict_, table_name):
    # Write a dict to the DB this only works if the dict keys match the db column names
    if dict_:
        # make sure there are no keys in post_data which are not in the db
        table_info = db.execute(f"pragma table_info({table_name})")
        a = list(dict_.keys())
        b = [o[1] for o in table_info]
        for i in a:
            if i not in b:
                dict_.pop(i)
        # Construct the SQL Query
        keys = list(dict_.keys())
        c = ""
        for i in range(len(keys) + 1):
            c = c + "?,"
        _ = list(dict_.values())
        _.insert(0, str(get_now_formatted()))
        db.execute(f"INSERT INTO {table_name} (date, {','.join(keys)}) VALUES({c[:-1]})", tuple(_))
        return 200


# Advanced version
def sql_write_timeline_posts(post_data):
    table_name = "timeline_posts"
    _build_write_sql_query(dict_=post_data, table_name=table_name)


def sql_write_mentions_meta(mentions_data):
    table_name = "mentions"
    _build_write_sql_query(dict_=mentions_data, table_name=table_name)


def sql_write_ai_params(ai_params):
    table_name = "ai_params"
    _build_write_sql_query(dict_=ai_params, table_name=table_name)


def sql_write_replied_tweet_meta(tweet_data):
    table_name = "replied_tweets"
    _build_write_sql_query(dict_=tweet_data, table_name=table_name)


def sql_check_text_already_replied(hash_):
    hash_ = str(hash_)
    """ controls if user already followed before """
    if (
            db.execute(
                "SELECT EXISTS(SELECT 1 FROM replied_tweets WHERE input_tweet_hash='"
                + hash_
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return True
    return False


def sql_news_already_posted(hash_, url=None):
    _ = []
    hash_ = str(hash_)
    url = str(url)

    if (db.execute(
            "SELECT EXISTS(SELECT 1 FROM timeline_posts WHERE input_text_hash='" + hash_ + "' LIMIT 1)").fetchone()[
        0] > 0):
        _.append(True)
    if url and (
            db.execute(
                "SELECT EXISTS(SELECT 1 FROM timeline_posts WHERE input_text_url='"
                + url
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        _.append(True)

    if _ and sum(_) == len(_):
        return True
    else:
        return False


def sql_mention_already_asnwered(tweet_id):
    id = str(tweet_id)

    if (
            db.execute(
                "SELECT EXISTS(SELECT 1 FROM mentions WHERE in_reply_to_status_id='"
                + id
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return True
    return False


def delete_duplicates():
    query = 'select count(username_id) from usernames group by username_id having (count(username_id) > 1 );'
    db.execute(query)


# def write_profile_snapshot(db, user_info):
#     timestamp = datetime.utcnow()
#     user = user_info['username']
#     edge_followed_by = user_info['edge_followed_by']['count']
#     edge_follow = user_info['edge_follow']['count']
#     edge_owner_to_timeline_media = user_info['edge_owner_to_timeline_media']['count']
#     follower_following_ratio = int(edge_followed_by) / int(edge_follow)
#
#     db.execute(
#         "INSERT INTO profile (snap_shot_timestamp,user, edge_followed_by, edge_follow, edge_owner_to_timeline_media, follower_following_ratio) VALUES(?,?,?,?,?,?)",
#         (timestamp, str(user), int(edge_followed_by), int(edge_follow), int(edge_owner_to_timeline_media),
#          float(follower_following_ratio))
#     )
#
#
# def write_replied_tweets_activity_sql(db, type_, owner_id, media_id=0, media_shortcode=0, comment_text=0, timestamp=0,
#                                       hashtag=0):
#     if timestamp == 0:
#         timestamp = datetime.utcnow()
#
#     if media_id == float('nan'):
#         media_id = 0
#     if media_shortcode == float('nan'):
#         media_shortcode = 0
#     if comment_text == float('nan'):
#         comment_text = 0
#     if hashtag == 0 or hashtag == float('nan'):
#         hashtag = str(current_tag)
#
#     db.execute(
#         "INSERT INTO replied_tweets (action_time, type, owner_id, media_id,media_shortcode, comment_text, hashtag ) VALUES(?,?,?,?,?,?,?)",
#         (timestamp, str(type_), int(owner_id), int(media_id), str(media_shortcode), str(comment_text), hashtag)
#         )
#
#
# def write_mentions_activity_sql(db, activity_dict):
#     timestamp = activity_dict['response_time']
#
#     response_action = activity_dict['response_action']
#     response_user_id = activity_dict['response_user_id']
#     response_username = activity_dict['response_username']
#     response_text = activity_dict['response_text']
#     response_media_id = activity_dict['response_media_id']
#     response_media_shortcode = activity_dict['response_media_shortcode']
#
#     if response_action is float('nan'):
#         response_action = 0
#     if response_user_id is float('nan'):
#         response_user_id = 0
#     if response_username is float('nan'):
#         response_username = 0
#     if response_text is float('nan'):
#         response_text = 0
#     if response_media_id is float('nan'):
#         response_media_id = 0
#     if response_media_shortcode is float('nan'):
#         response_media_shortcode = 0
#
#     db.execute(
#         "INSERT INTO mentions (response_time, response_action, response_user_id, response_username, response_text, response_media_id, response_media_shortcode) VALUES(?,?,?,?,?,?,?)",
#         (timestamp, str(response_action), int(response_user_id), str(response_username), str(response_text),
#          int(response_media_id), str(response_media_shortcode))
#     )
#
#
# # def check_user_already_commented(db, owner_id):
# #     owner_id = int(owner_id)
# #     check = db.execute(f"SELECT type from replied_tweets WHERE owner_id={owner_id}").fetchone()
# #     if check is None:
# #         return False
# #     elif check[0] == 'GraphCommentMediaStory':
# #         return True
# #     else:
# #         return False
#
# def dict_factory(cursor, row):
#     d = {}
#     for idx, col in enumerate(cursor.description):
#         d[col[0]] = row[idx]
#     return d
#
#
# def check_user_already_commented(db, owner_id):
#     check = db.execute(f"SELECT type from replied_tweets WHERE owner_id={owner_id}").fetchall()
#     if len(check) == 0:
#         return False
#     else:
#         target = 'GraphCommentMediaStory'
#         for i in check:
#             if i[0] == target:
#                 return True
#         return False
#
#
# def check_media_alredy_commented(db, media_id):
#     media_id = int(media_id)
#     check = db.execute(f"SELECT type from replied_tweets WHERE media_id={media_id}").fetchall()
#     if len(check) == 0:
#         return False
#     else:
#         target = 'GraphCommentMediaStory'
#         for i in check:
#             if i[0] == target:
#                 return True
#         return False
#
#
# def check_already_liked(db, media_id):
#     """ controls if media already liked before """
#     media_id = int(media_id)
#     check = db.execute(f"SELECT type from replied_tweets WHERE media_id={media_id}").fetchall()
#     if len(check) == 0:
#         return False
#     else:
#         target = 'GraphLikeAggregatedStory'
#         for i in check:
#             if i[0] == target:
#                 return True
#         return False
#
#
# def check_already_followed(db, user_id):
#     user_id = str(user_id)
#     """ controls if user already followed before """
#     if (
#             db.execute(
#                 "SELECT EXISTS(SELECT 1 FROM usernames WHERE username_id='"
#                 + user_id
#                 + "' LIMIT 1)"
#             ).fetchone()[0]
#             > 0
#     ):
#         return True
#     return False
#
#
# def check_already_unfollowed(db, user_id):
#     """ controls if user was already unfollowed before """
#     if (
#             db.execute(
#                 "SELECT EXISTS(SELECT 1 FROM usernames WHERE username_id='"
#                 + user_id
#                 + "' AND unfollow_count > 0 LIMIT 1)"
#             ).fetchone()[0]
#             > 0
#     ):
#         return True
#     return False
#
#

#
#
# def insert_media_like(db, media_id, status):
#     count = db.execute(f"select count(*) from medias WHERE media_id = {media_id}").fetchone()
#     if count[0] > 0:
#         db.execute(f"UPDATE medias SET liked ='1' WHERE media_id={media_id}")
#     else:
#         """ insert media to medias """
#         liked = 1
#         db.execute("INSERT INTO medias (media_id, status, datetime, liked) VALUES(?,?,?,?)",
#                    (media_id, status, str(get_now()), liked))
#     # UPDATE medias SET liked = 0 WHERE status != 200;
#
#
# def insert_media_comment(db, media_id, status):
#     count = db.execute(
#         f"select count(*) from medias WHERE media_id = {media_id}").fetchone()
#     if count[0] > 0:
#         db.execute(f"UPDATE medias SET commented ='1' WHERE media_id= {media_id}")
#     else:
#         status = int(status)
#         """ insert media to medias """
#         commented = 1
#         db.execute("INSERT INTO medias (media_id, status, datetime, commented) VALUES(?,?,?,?)",
#                    (media_id, status, str(get_now()), commented))
#
#
# def insert_username(db, user_id, username):
#     username = str(username)
#     user_id = str(user_id)
#     """ insert user_id to usernames """
#     db.execute(
#         "INSERT INTO usernames (username_id, username, last_followed_time) VALUES('"
#         + user_id
#         + "','"
#         + username
#         + "','"
#         + str(get_now())
#         + "')")
#
#
# def reset_unfollow_count(db, user_id=False, username=False):
#     if user_id:
#         qry = (
#                 "UPDATE usernames  SET unfollow_count = 0 \
#                   WHERE username_id ='"
#                 + user_id
#                 + "'"
#         )
#         db.execute(qry)
#     elif username:
#         qry = (
#                 "UPDATE usernames \
#                   SET unfollow_count = 0 \
#                   WHERE username ='"
#                 + username
#                 + "'"
#         )
#         db.execute(qry)
#     else:
#         raise ValueError('One of username, user_id must be given')
#
#
# def insert_unfollow_count(db, user_id=False, username=False):
#     """ track unfollow count for new futures """
#     if user_id:
#         qry = (
#                 "UPDATE usernames \
#                   SET unfollow_count = unfollow_count + 1 \
#                   WHERE username_id ='"
#                 + user_id
#                 + "'"
#         )
#         db.execute(qry)
#     elif username:
#         qry = (
#                 "UPDATE usernames \
#                   SET unfollow_count = unfollow_count + 1 \
#                   WHERE username ='"
#                 + username
#                 + "'"
#         )
#         db.execute(qry)
#     else:
#         return False
#
#
# def get_usernames_first(db):
#     """ Gets first element of usernames table """
#     username = db.execute("SELECT * FROM usernames LIMIT 1")
#     if username:
#         return username
#     else:
#         return False
#
#
# def get_usernames(db):
#     """ Gets usernames table """
#     usernames = db.execute("SELECT * FROM usernames")
#     if usernames:
#         return usernames
#     else:
#         return False
#
#
# def get_username_random(db):
#     """ Gets random username """
#     username = db.execute(
#         "SELECT * FROM usernames WHERE unfollow_count=0 ORDER BY RANDOM() LIMIT 1"
#     ).fetchone()
#     if username:
#         return username
#     else:
#         return False
#
#
# def insert_last_unfollow_check(db, user_id):
#     qry = f"UPDATE usernames SET last_unfollow_check = '{str(get_now())}' WHERE username_id ='{user_id}' "
#     db.execute(qry)
#
#
# def get_username_to_unfollow_random(db):
#     """ Gets random username that is older than follow_time and has zero unfollow_count """
#     cut_off_time = get_now() - timedelta(seconds=follow_time)
#     username = db.execute("SELECT * FROM usernames \
#                                             WHERE DATETIME(last_followed_time) < DATETIME('" + str(cut_off_time) + "')\
#                                             AND DATETIME(last_unfollow_check) < DATETIME('" + str(cut_off_time) + "')\
#                                             AND unfollow_count=0\
#                                             ORDER BY RANDOM() LIMIT 1").fetchone()
#     if username:
#         insert_last_unfollow_check(db, user_id=username[0])
#         return username
#     elif follow_time_enabled is False:
#         username = db.execute("SELECT * FROM usernames WHERE unfollow_count=0 ORDER BY RANDOM() LIMIT 1").fetchone()
#         if username:
#             insert_last_unfollow_check(db, user_id=username[0])
#             return username
#         else:
#             return False
#     else:
#         return False
#
#
# def get_username_to_unfollow(db):
#     """ Gets username that is older than follow_time and has zero unfollow_count """
#     cut_off_time = get_now() - timedelta(seconds=follow_time)
#     username = db.execute("SELECT * FROM usernames WHERE \
#                                         unfollow_count=0 \
#                                         AND DATETIME(last_unfollow_check) < DATETIME('" + str(cut_off_time) + "')\
#                                         AND DATETIME(last_followed_time) < DATETIME('" + str(cut_off_time) + "')"
#                           ).fetchall()
#
#     if username:
#         insert_last_unfollow_check(db, user_id=username[0])
#         return username
#     else:
#         return False
#
#
# def get_username_row_count(db):
#     """ Gets the number of usernames in table """
#     count = db.execute("select count(*) from usernames").fetchone()
#     if count:
#         return count[0]
#     else:
#         return False
#
#
# def get_medias_to_unlike(db):
#     """ Gets random medias that is older than unlike_time"""
#     cut_off_time = get_now() - timedelta(seconds=time_till_unlike)
#     media = db.execute(
#         "SELECT media_id FROM medias WHERE \
#     DATETIME(datetime) < DATETIME('"
#         + str(cut_off_time)
#         + "') \
#     AND status=200 ORDER BY RANDOM() LIMIT 1"
#     ).fetchone()
#     if media:
#         return media[0]
#     return False
#
#
# def update_media_complete(db, media_id):
#     """ update media to medias """
#     qry = "UPDATE medias SET status='201' WHERE media_id ='" + media_id + "'"
#     db.execute(qry)
#
#
# def check_if_userid_exists(db, userid):
#     """ Checks if username exists """
#     # print("select count(*) from usernames WHERE username_id = " + userid)
#     count = db.execute(
#         "select count(*) from usernames WHERE username_id = " + userid
#     ).fetchone()
#     if count:
#         if count[0] > 0:
#             return True
#         else:
#             return False
#     else:
#         return False
#
#
# def insert_user_agent(db, user_agent):
#     count = db.execute("select count(*) from settings WHERE settings_name = 'USERAGENT'").fetchone()
#     if count[0] < 1:
#         db.execute("INSERT INTO settings (settings_name) VALUES('USERAGENT')")
#     db.execute(f" UPDATE settings SET settings_val = '{user_agent}' WHERE settings_name = 'USERAGENT' ")
#     return user_agent
#
#
# def get_user_agent_db(db):
#     """ Check user agent  """
#     qry = "SELECT settings_val from settings where settings_name = 'USERAGENT'"
#     result_check = db.execute(qry).fetchone()
#     try:
#         if str(result_check[0]).startswith('Mozilla'):
#             return str(result_check[0])
#         else:
#             raise TypeError
#     except TypeError:
#         return False
#
#
# def clean_folder(db, folder_to_clean, identifier_keyword=None, max_files_to_keep=5):
#     if datetime.utcnow().hour % 8 == 0 and 0 < datetime.utcnow().minute <= 2:
#         arr = os.listdir(folder_to_clean)
#         if identifier_keyword:
#             arr = [x for x in arr if identifier_keyword in x]
#         arr = sorted(arr)
#         if len(arr) > max_files_to_keep:
#             for i in arr[max_files_to_keep:]:
#                 os.remove(folder_to_clean + i)


def sqlite3_backup(db, dbfile_path, backup_folder='data/backupdata/'):
    """Create timestamped database copy"""

    if datetime.utcnow().hour % 8 == 0 and 0 < datetime.utcnow().minute <= 2:
        # db.execute('begin immediate')

        bk_time_stamp = str(datetime.utcnow().strftime("%Y_%m_%d_%H_%M"))
        bk_path = dbfile_path.split('.')
        bk_path = bk_path[0] + '_' + bk_time_stamp + '.' + bk_path[1]

        # Make new backup file
        shutil.copyfile(dbfile_path, backup_folder + bk_path)
        print("\nCreating {}...".format(bk_path))
        # Unlock database
        # connection.rollback()
        # db.rollback()
    else:
        print(f'No DB Backup Needed')
