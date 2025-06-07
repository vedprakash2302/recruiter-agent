from typing import Dict
from threading import Lock

# Thread-safe global store for tracking cv and job details
CV_DETAILS = {}
JOB_DETAILS = {}
global_lock = Lock()