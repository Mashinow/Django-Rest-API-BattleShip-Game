import json
from os import getcwd


class LocalConfig:
    def __init__(self):
        self.path = getcwd() + r'/resources/config.json'
        self.parse_json_values()

    def parse_json_values(self):
        with open(self.path, 'r') as file:
            data = json.load(file)
        if not data:
            return
        for key, value in data.items():
            setattr(self, key, value)

    def update_json_file(self, valDict):
        with open(self.path, 'r') as file:
            data = json.load(file)
        for key, value in valDict.items():
            data[key] = value
            setattr(self, key, value)
        with open(self.path, 'w') as file:
            json.dump(data, file, indent=4)


if __name__ == '__main__':
    LocalConfig()
