import argparse
import json
import logging
import os
from backend.todo_list import TodoList
from backend.todo_item import TodoItem
import sys

logging.basicConfig(level=logging.INFO)

def generate_api_doc():
    api_doc = """
Todo List API Documentation

### Overview

The Todo List API provides a simple and efficient way to manage a list of todo items.

### Endpoints

#### 1. GET /todo/list

Returns a list of all todo items in the system.

#### 2. POST /todo/new

Creates a new todo item.

#### 3. GET /todo/update

Updates an existing todo item.

#### 4. DELETE /todo/delete

Deletes a todo item.

### Request Body

* `description`: The description of the todo item.

### Response

* `200 OK`: The todo item was created/updated/deleted successfully.
* `400 Bad Request`: The request was invalid.
* `404 Not Found`: The todo item was not found.

### Usage

You can use the following command-line tools to interact with the Todo List API:
* `todo list` to display all todo items
* `todo new <description>` to create a new todo item
* `todo update <index> <description>` to update an existing todo item
* `todo delete <index>` to delete a todo item
"""
    return api_doc

def update_api_doc(new_api_doc):
    return new_api_doc

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    run_parser = subparsers.add_parser('run')
    run_parser.set_defaults(command='run')

    main_parser = subparsers.add_parser('main')
    main_parser.set_defaults(command='main')

    init_parser = subparsers.add_parser('init')
    init_parser.add_argument('config', help='path to configuration file')
    init_parser.add_argument('list', help='load todo list from file')
    init_parser.add_argument('new', help='new todo item')
    init_parser.add_argument('update', help='update existing todo item')
    init_parser.add_argument('delete', help='delete todo item')
    init_parser.add_argument('run', action='store_true', default=False, help='run todo app')
    init_parser.add_argument('main', action='store_true', default=False, help='run main entry point')

    args = parser.parse_args()

    if args.command == 'run':
        todo_list = TodoList()
        todo_list.load_from_file('todo_list.txt')
        while True:
            command = input('Enter command (run, main, init, quit): ').strip()
            if command in ['run', 'main']:
                todo_list.run()
            elif command == 'init':
                todo_list.init(args.config, args.list, args.new, args.update, args.delete)
            elif command == 'quit':
                break
            else:
                logging.error("Unknown command")
    elif args.command == 'main':
        todo_list = TodoList()
        todo_list.load_from_file('todo_list.txt')
        todo_list.run()
    elif args.command == 'init':
        todo_list = TodoList()
        todo_list.load_from_file('todo_list.txt')
        todo_list.init(args.config, args.list, args.new, args.update, args.delete)
    else:
        logging.error("Unknown command")

class TodoApp:
    def __init__(self):
        self.todo_list = TodoList()

    def init(self, config, list, new, update, delete):
        if config:
            with open(config, 'r') as config_file:
                config = json.load(config_file)
                self.todo_list.load_from_config(config)
        if list:
            self.todo_list.load_from_file(list)
        if new:
            self.todo_list.add_todo_item(TodoItem(new))
        if update:
            try:
                index = int(update.split(',')[0]) - 1
                description = update.split(',')[1]
                remove_todo_item(self.todo_list, index)
                add_todo_item(self.todo_list, description)
            except ValueError:
                logging.error("Invalid update format")
        if delete:
            try:
                index = int(delete.split(',')[0]) - 1
                remove_todo_item(self.todo_list, index)
            except ValueError:
                logging.error("Invalid delete format")

    def run(self):
        self.init()
        while True:
            command = input('Enter command (run, main, init, quit): ').strip()
            if command in ['run', 'main']:
                self.todo_list.run()
            elif command == 'init':
                self.init()
            elif command == 'quit':
                break
            else:
                logging.error("Unknown command")

    def main(self):
        self.run()

if __name__ == '__main__':
    app = TodoApp()
    app.init()
    app.run()