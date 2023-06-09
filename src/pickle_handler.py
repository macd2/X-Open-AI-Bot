import pickle
from datetime import datetime, timedelta
from pathlib import Path

from src.communication_handler import logger


class FileExpiredError(Exception):
    pass


class FileNotFoundError(Exception):
    pass


def is_file_older_than(file, delta):
    cutoff = datetime.utcnow() - delta
    mtime = datetime.utcfromtimestamp(Path(file).stat().st_mtime)
    return mtime < cutoff


def write_pickle(obj, filename, hashtag=None):
    path = f'./storage/{filename}.pickle'
    logger.info(f"Write pickle to: {path}")
    if hashtag:
        for i in obj:
            i['hashtag'] = hashtag
    with open(path, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(filename, max_file_age_hrs=10):
    path = f'./storage/{filename}.pickle'
    logger.info(f"Loading pickle from: {path}")
    if Path(path).is_file():
        if is_file_older_than(path, timedelta(hours=max_file_age_hrs)):
            raise FileExpiredError("File is older than specified")
        with open(path, 'rb') as handle:
            return pickle.load(handle)
    raise FileNotFoundError('File does not exist')
