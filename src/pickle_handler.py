import logging
import pickle
from os.path import exists, getmtime
from datetime import datetime, timedelta



logger = logging.getLogger()

def is_file_older_than(file, delta):
    cutoff = datetime.utcnow() - delta
    mtime = datetime.utcfromtimestamp(getmtime(file))
    if mtime < cutoff:
        logger.info(f"File is older than {delta} hours")
        return True
    return False


def write_pickle(obj, filename, hashtag=None):
    path = f'./storage/{filename}.pickle'
    logger.info(f"Write pickle to {path}")
    if hashtag:
        for i in obj:
            i['hashtag'] = hashtag
    with open(path, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def laod_pickle(filename, max_file_age_hrs=10):
    path = f'./storage/{filename}.pickle'
    if exists(path):
        if is_file_older_than(path, timedelta(hours=max_file_age_hrs)):
            raise Exception("File is older than specified")

        logger.info(f"Load pickle from {path}")
        with open(path, 'rb') as handle:
            return pickle.load(handle)
    raise Exception('File does not exist')
