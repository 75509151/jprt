import queue
from .dbm import get_db_instance

__all__ = ["DB_POOL"]


class DbPool(object):
    """docstring for DbPool"""
    # TODO: may be need auto auto creat

    def __init__(self, count=20, auto_get=True):
        # count = 20
        db_queue = queue.Queue(count)
        for i in range(count):
            db = get_db_instance()
            db_queue.put(db)
        self._queue = db_queue
        self.item = self._queue.get() if auto_get else None

    def __enter__(self):
        if self.item is None:
            self.item = self._queue.get()
        return self.item

    def __exit__(self, Type, value, traceback):
        if self.item is not None:
            self._queue.put(self.item)
            self.item = None

    def __del__(self):
        if self.item is not None:
            self._queue.put(self.item)
            self.item = None


DB_POOL = DbPool(20)


if __name__ == '__main__':

    db_pool = DbPool(count=20)
    with db_pool as db:
        print(db)
    for i in range(40):
        with db_pool as db:
            print(db)

