from backend.todo_list import TodoList
from backend.todo_item import TodoItem
import argparse
import json
import logging
import sys

logging.basicConfig(level=logging.INFO)

class TodoApp:
    def __init__(self):
        self.todo_list = TodoList()

    def init(self, args=None):
        if args is None:
            parser = argparse.ArgumentParser()
            parser.add_argument('-c', '--config', help='path to configuration file')
            parser.add_argument('-l', '--list', help='load todo list from file')
            parser.add_argument('-n', '--new', help='new todo item')
            parser.add_argument('-u', '--update', help='update existing todo item')
            parser.add_argument('-d', '--delete', help='delete todo item')
            parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
            parser.add_argument('run', help='run todo app')
            parser.add_argument('main', help='run main entry point')
            parser.add_argument('init', help='initialize todo app')
            args = parser.parse_args()
        if args.config:
            with open(args.config, 'r') as config_file:
                config = json.load(config_file)
                self.todo_list.load_from_config(config)
        if args.list:
            self.todo_list.load_from_file(args.list)
        if args.new:
            self.todo_list.add_todo_item(TodoItem(args.new))
        if args.update:
            self.todo_list.update_todo_item(args.update)
        if args.delete:
            self.todo_list.delete_todo_item(args.delete)

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
                print('Unknown command')

    def main(self):
        self.run()

if __name__ == '__main__':
    app = TodoApp()
    app.init()
    app.run()