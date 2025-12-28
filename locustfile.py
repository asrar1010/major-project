from locust import HttpUser, task, between

class BackendUser(HttpUser):
    # No random wait — constant pressure
    wait_time = between(0.01, 0.01)

    @task
    def hit_root(self):
        self.client.get("/")
