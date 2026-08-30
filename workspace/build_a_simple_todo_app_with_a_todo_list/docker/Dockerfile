import logging
from docker import Docker
import subprocess

def load_todo_list(filename):
    try:
        todo_list = TodoList()
        todo_list.load_from_file(filename)
        return todo_list
    except Exception as e:
        logging.error(f"Error loading todo list from file: {e}")
        return None

def save_todo_list(todo_list, filename):
    try:
        with open(filename, 'w') as file:
            file.write('\n'.join(todo_list.items))
    except Exception as e:
        logging.error(f"Error saving todo list to file: {e}")

def add_todo_item(todo_list, item):
    todo_list.add_todo_item(item)

def remove_todo_item(todo_list, index):
    todo_list.delete_todo_item(index)

def main():
    docker = Docker()
    docker.load_image('python:3.9-slim')
    docker.exec_create('python', '-m', 'todo_app', '--run', '-c', 'todo_list.txt')
    docker.exec_create('python', '-m', 'todo_app', '--run', '-m', 'main')

if __name__ == '__main__':
    main()