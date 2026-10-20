import unittest
from backend.todo_list import TodoList
from backend.todo_item import TodoItem
import logging

logging.basicConfig(level=logging.INFO)

class TestTodoList(unittest.TestCase):

    def test_todo_list_init(self):
        todo_list = TodoList()
        self.assertEqual(len(todo_list.items), 0)

    def test_todo_item_init(self):
        item = TodoItem("Test item")
        self.assertEqual(item.description, "Test item")

    def test_add_todo_item(self):
        todo_list = TodoList()
        item = TodoItem("Test item")
        todo_list.add_todo_item(item)
        self.assertEqual(len(todo_list.items), 1)

    def test_remove_todo_item(self):
        todo_list = TodoList()
        item = TodoItem("Test item")
        todo_list.add_todo_item(item)
        todo_list.delete_todo_item(0)
        self.assertEqual(len(todo_list.items), 0)

class TestTodoItem(unittest.TestCase):

    def test_todo_item_init(self):
        item = TodoItem("Test item")
        self.assertEqual(item.description, "Test item")

    def test_todo_item_str(self):
        item = TodoItem("Test item")
        self.assertEqual(str(item), "Test item")

class TestTodoListFunctions(unittest.TestCase):

    def test_load_todo_list(self):
        todo_list = TodoList()
        self.assertIsNone(todo_list.load_from_file("non-existent-file.txt"))

    def test_save_todo_list(self):
        todo_list = TodoList()
        todo_list.items = ["Test item 1", "Test item 2"]
        save_todo_list(todo_list, "test_list.txt")
        with open("test_list.txt", 'r') as file:
            self.assertEqual(file.read(), "Test item 1\nTest item 2\n")

    def test_add_todo_item(self):
        todo_list = TodoList()
        todo_list.add_todo_item("Test item")
        self.assertEqual(len(todo_list.items), 1)

    def test_remove_todo_item(self):
        todo_list = TodoList()
        todo_list.add_todo_item("Test item")
        todo_list.delete_todo_item(0)
        self.assertEqual(len(todo_list.items), 0)

if __name__ == '__main__':
    unittest.main()