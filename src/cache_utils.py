import json
import os
import time
from datetime import datetime

# Create memory cache for session use
MEMORY_CACHE = {}


def get_cached_data(key, max_age_seconds=3600):
    """Get data from memory cache if not expired"""
    if key in MEMORY_CACHE:
        timestamp, data = MEMORY_CACHE[key]
        if time.time() - timestamp < max_age_seconds:
            return data
    return None


def cache_data(key, data):
    """Store data in memory cache with timestamp"""
    MEMORY_CACHE[key] = (time.time(), data)
    return True
