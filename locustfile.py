import string

from locust import HttpUser, task, between
import random


class UserBehavior(HttpUser):
    wait_time = between(1, 2.5)

    def on_start(self):
        name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        email = name + "@example.com"
        password = "password"
        self.client.post('/register', data={'name': name, 'email': email, 'password': password})

        response = self.client.post('/login', data={'email': email, 'password': password})
        self.token = response.json()['response']['token']
        self.task_ids = []

    @task
    def add_task(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.post('/add-task', data={'task': 'Test Task'}, headers=headers)
        assert response.status_code == 200, "Unexpected status code: " + str(response.status_code)
        task_id = response.json()['task']['id']
        assert isinstance(task_id, int), "Task ID is not an integer: " + str(task_id)
        self.task_ids.append(task_id)

    @task
    def get_tasks(self):
        print(self.token)
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/task', headers=headers)
        tasks = response.json()['tasks']
        self.task_ids = [single_task['id'] for single_task in tasks]

    # @task
    # def delete_task(self):
    #     if self.task_ids:
    #         task_id = random.choice(self.task_ids)
    #         headers = {'Authorization': f'Bearer {self.token}'}
    #         self.client.get(f'/remove-task/{task_id}', headers=headers)
    #         self.task_ids.remove(task_id)
    #
    # @task
    # def mark_task_done(self):
    #     if self.task_ids:
    #         task_id = random.choice(self.task_ids)
    #         headers = {'Authorization': f'Bearer {self.token}'}
    #         self.client.patch(f'/mark-done/{task_id}', headers=headers)
    #
    # @task
    # def update_task(self):
    #     if self.task_ids:
    #         task_id = random.choice(self.task_ids)
    #         headers = {'Authorization': f'Bearer {self.token}'}
    #         self.client.put(f'/edit-task/{task_id}', data={'task': 'Updated Task'}, headers=headers)

    # @task
    # def logout(self):
    #     headers = {'Authorization': f'Bearer {self.token}'}
    #     self.client.get('/logout', headers=headers)
