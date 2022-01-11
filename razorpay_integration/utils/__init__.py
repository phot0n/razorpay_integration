import math
import time


def get_epoch_time() -> int:
	# returns the current epoch time
	return math.ceil(time.time())

def add_to_epoch(seconds: int) -> int:
	# adds seconds to the current epoch time
	return get_epoch_time() + seconds

def convert_epoch_to_timestamp(epoch_time: int):
	# converts any given epoch time to human readable datetime
	return time.ctime(epoch_time)
