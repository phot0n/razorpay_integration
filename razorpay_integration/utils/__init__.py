import math
import time


def get_epoch_time() -> int:
	return math.ceil(time.time())

def add_to_epoch(seconds: int) -> int:
	return get_epoch_time() + seconds

def convert_epoch_to_timestamp(epoch_time: int):
	return time.ctime(epoch_time)
