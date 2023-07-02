import os
import shutil
import sqlite3
from datetime import datetime

from dotenv import dotenv_values

env = dotenv_values(".env")


def connect_to_local_db():
    conn = sqlite3.connect(f"./storage/{env['db_name']}.db", timeout=5, isolation_level=None)
    return conn


# import psycopg2
#
#
# def connect_to_remote_db(host, port, database, username, password):
#     try:
#         conn = psycopg2.connect(
#             host=host,
#             port=port,
#             database=database,
#             user=username,
#             password=password,
#         )
#         # Return the connection object
#         return conn
#     except psycopg2.Error as e:
#         print(f"Error connecting to PostgreSQL: {e}")
#         return None


# def connect_to_db(remote=False, db_name=None, host=None, port=None, user_name=None, password=None):
#     # ToDo Fix the remote connector
#     if remote and db_name and host and port and password and user_name:
#         logger.info("Connect to Remote DB")
#         raise NotImplementedError
#         # return connect_to_remote_db(host, port, db_name, user_name, password)
#     else:
#         logger.info("Connect to local DB")
#         return connect_to_local_db()
#
#
# db = connect_to_db(remote=False, db_name=env['sql_db_name'], host=env['sql_host'], port=env['sql_port'],
#                    user_name=env['sql_user'], password=env['sql_pass'])

db = connect_to_local_db()


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


def sql_get_n_latest_records(table_name, column_name, n):
    _ = db.execute(f"SELECT {str(column_name)} FROM {str(table_name)} order by date desc LIMIT {n};").fetchall()
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
                        "raw_model_response", "output_tweet_id", "output_to_username", "status"]},
            {"name": "ai_params",
             "fields": ["question", "prompt", "response", "personality", "nuance", "mood", "rules","model", "temperature",
                        "ability", "filter"]},
            {"name": "timeline_posts",
             "fields": ["search_term", "news_date","body", "body_hash", "description_hash", "input_text_url", "output_text",
                        "post_tweet_id", "status"]}
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
            "SELECT EXISTS(SELECT 1 FROM timeline_posts WHERE input_text_hash='" + hash_ + "' LIMIT 1)").fetchone()[0] > 0):
        _.append(True)
    if url and (
            db.execute(
                "SELECT EXISTS(SELECT 1 FROM timeline_posts WHERE input_text_url='"
                + url
                + "' LIMIT 1)"
            ).fetchone()[0] > 0):
        _.append(True)

    if _ and all(_):
        return True
    else:
        return False


def sql_mention_already_answered(tweet_id):
    hash_ = str(tweet_id)

    if (
            db.execute(
                "SELECT EXISTS(SELECT 1 FROM mentions WHERE in_reply_to_status_id='"
                + hash_
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return True
    return False


def sql_already_in_db(table_name, columne, value):
    if (
            db.execute(
                f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {columne}='"
                + str(value)
                + "' LIMIT 1)"
            ).fetchone()[0]
            > 0
    ):
        return True
    return False


def delete_duplicates():
    query = 'select count(username_id) from usernames group by username_id having (count(username_id) > 1 );'
    db.execute(query)


def sqlite3_backup(db_file_path, backup_folder='./storage'):
    current_time = datetime.utcnow()

    if current_time.minute <= 2 and current_time.hour % 8 == 0:
        bk_time_stamp = current_time.strftime("%Y_%m_%d_%H_%M")
        bk_path = os.path.join(backup_folder,
                               f"{os.path.splitext(db_file_path)[0]}_{bk_time_stamp}{os.path.splitext(db_file_path)[1]}")

        shutil.copyfile(db_file_path, bk_path)
        print(f"Creating {bk_path}...")
    else:
        print("No DB Backup Needed")


def sync_databases(source_db, target_db, two_way_sync=True):
    # Establish connections to the source and target databases
    conn_source = sqlite3.connect(source_db)
    conn_target = sqlite3.connect(target_db)

    # Set up cursors for the source and target databases
    cursor_source = conn_source.cursor()
    cursor_target = conn_target.cursor()

    # Fetch all tables from the source database
    cursor_source.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor_source.fetchall()

    # Iterate over each table and synchronize the data
    for table in tables:
        table_name = table[0]

        # Retrieve the column names and types for the source table
        cursor_source.execute(f"PRAGMA table_info({table_name});")
        columns = cursor_source.fetchall()
        column_names = [column[1] for column in columns]

        # Retrieve all rows from the source table
        cursor_source.execute(f"SELECT * FROM {table_name};")
        rows_source = cursor_source.fetchall()

        # Retrieve all rows from the target table
        cursor_target.execute(f"SELECT * FROM {table_name};")
        rows_target = cursor_target.fetchall()

        # Synchronize the data from the source to the target database
        for row_source in rows_source:
            if row_source not in rows_target:
                placeholders = ', '.join(['?' for _ in row_source])
                insert_query = f"INSERT INTO {table_name} VALUES ({placeholders});"
                cursor_target.execute(insert_query, row_source)

        # Perform two-way synchronization if enabled
        if two_way_sync:
            # Synchronize the data from the target to the source database
            for row_target in rows_target:
                if row_target not in rows_source:
                    placeholders = ', '.join(['?' for _ in row_target])
                    insert_query = f"INSERT INTO {table_name} VALUES ({placeholders});"
                    cursor_source.execute(insert_query, row_target)

    # Commit the changes to both databases
    conn_source.commit()
    conn_target.commit()

    # Close the connections
    conn_source.close()
    conn_target.close()
