import requests
from http import HTTPStatus
import json
from objects import GlobalObjects


class RequestManager:
    def __init__(self, obj: GlobalObjects):
        self.gObj = obj
        self.config = self.gObj.config
        self.baseUrl = self.config.baseUrl
        self.token = ''
        self.session = requests

    def send_request(self, method, url, data=None, header=None, log=True):
        answer = None
        try:
            if method == 'GET':
                response = self.session.get(url, params=data, verify=False, headers=header)
            elif method == 'POST':
                response = self.session.post(url, data=data, verify=False, headers=header)
            else:
                raise ValueError("Unsupported HTTP method")

        except Exception as e:
            self.gObj.send_log_msg(f"Произошло исключение: {e}")
            return None

        if response.status_code == HTTPStatus.OK:
            answer = json.loads(response.text)
        elif log:
            self.gObj.send_log_msg(response.text)

        return answer

    def send_get(self, url, params=None, header=None, log=True):
        return self.send_request('GET', url, params, header, log)

    def send_post(self, url, data, header=None, log=True):
        return self.send_request('POST', url, data, header, log)

    def send_json_post(self, url, data, log=True):
        headers = {'Content-Type': 'application/json'}
        data_json = json.dumps(data)
        return self.send_post(url, data_json, headers, log)

    def login_process(self, login, password) -> bool:
        loginUrl = self.baseUrl + self.config.loginUrl
        answer = self.send_post(loginUrl, {'username': login, 'password': password})
        if answer:
            self.token = answer['auth_token']
            self.session = requests.Session()
            newHeader = {'Authorization': 'Token ' + self.token}
            self.session.headers.update(newHeader)
            return True
        else:
            return False


if __name__ == '__main__':
    pass
    # session = requests.Session()
    #
    # # Добавляем новый заголовок
    # new_header = {'Authorization': '12345'}
    # session.headers.update(new_header)
    #
    # # Теперь объект session содержит новый заголовок
    #
    # # Выводим заголовки
    # print(session.headers)
