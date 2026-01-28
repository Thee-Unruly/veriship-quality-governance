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
    
    @task
    def load_homepage(self):
        """Load the homepage."""
        self.client.get("/")
    
    @task(2)
    def load_api_endpoint(self):
        """Load a common API endpoint (weighted 2x)."""
        self.client.get("/api/projects/")
    
    # Add custom endpoints here
{custom_tasks}
