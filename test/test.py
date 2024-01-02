import unittest

from main import app, db, Task


class MyFlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()

    def tearDown(self):
        self.ctx.pop()

    def add_task(self):
        return self.client.post('/add-task', data={'task': 'Test Task'})

    def delete_task(self):
        return self.client.get('/remove-task/1')

    def test_add_task(self):
        response = self.add_task()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successfully Add Task', response.data)
        self.delete_task()

    def test_get_tasks(self):
        self.add_task()
        response = self.client.get('/task')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"tasks":[{"id":1,"is_done":false,"title":"Test Task"}]', response.data)
        self.delete_task()

    def test_mark_task_done(self):
        self.add_task()
        response = self.client.patch('/mark-done/1')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successfully Update Task', response.data)

        task = db.session.execute(db.select(Task).where(Task.id == 1)).scalar_one_or_none()
        self.assertTrue(task.is_done)
        self.delete_task()

    def test_404_given_unknown_id_when_mark_test_done(self):
        response = self.client.patch('/mark-done/2')
        print(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Task Not Found', response.data)

    def test_delete_task(self):
        self.add_task()
        response = self.client.get('/remove-task/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successfully Delete Task', response.data)

    def test_delete_task_404_not_found(self):
        response = self.client.get('/remove-task/1')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Task Not Found', response.data)

if __name__ == '__main__':
    unittest.main()
