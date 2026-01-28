"""
Locust load testing template file.
This file is dynamically generated based on user configuration.
"""

from locust import HttpUser, task, between


class LoadTestUser(HttpUser):
    """Simulated user for load testing."""
    
    # Wait time between requests (seconds)
    wait_time = between({min_wait}, {max_wait})
    
    # Base host URL (set dynamically)
    host = "{base_url}"
    
    # Custom endpoints (dynamically added)
{custom_tasks}
