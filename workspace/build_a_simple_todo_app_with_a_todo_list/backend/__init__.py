import argparse
import json
import logging

logging.basicConfig(level=logging.INFO)

class TodoItem:
    def __init__(self, description):
        self.description = description

    def __str__(self):
        return self.description

class TodoList:
    def __init__(self):
        self.items = []

    def load_from_config(self, config):
        self.items = config.get('items', [])

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                self.items = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            logging.error(f"File {filename} not found")

    def add_todo_item(self, item):
        self.items.append(str(item))

    def update_todo_item(self, index, description):
        if index < len(self.items):
            self.items[index] = str(TodoItem(description))
        else:
            logging.error(f"Index {index} out of range")

    def delete_todo_item(self, index):
        if index < len(self.items):
            del self.items[index]
        else:
            logging.error(f"Index {index} out of range")

    def run(self):
        for index, item in enumerate(self.items, start=1):
            print(f"{index}. {item}")

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='path to configuration file')
    parser.add_argument('-l', '--list', help='load todo list from file')
    parser.add_argument('-n', '--new', help='new todo item')
    parser.add_argument('-u', '--update', help='update existing todo item')
    parser.add_argument('-d', '--delete', help='delete todo item')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()
    if args.config:
        try:
            with open(args.config, 'r') as config_file:
                config = json.load(config_file)
                todo_list = TodoList()
                todo_list.load_from_config(config)
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
    elif args.list:
        todo_list = load_todo_list(args.list)
        if todo_list:
            todo_list.run()
    if args.new:
        add_todo_item(todo_list, args.new)
    if args.update:
        try:
            index = int(args.update.split(',')[0]) - 1
            description = args.update.split(',')[1]
            remove_todo_item(todo_list, index)
            add_todo_item(todo_list, description)
        except ValueError:
            logging.error("Invalid update format")
    if args.delete:
        try:
            index = int(args.delete.split(',')[0]) - 1
            remove_todo_item(todo_list, index)
        except ValueError:
            logging.error("Invalid delete format")
    if todo_list:
        todo_list.run()

if __name__ == '__main__':
    main()