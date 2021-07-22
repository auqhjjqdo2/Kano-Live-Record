import logging

import requests
from nacl import encoding, public
from base64 import b64encode

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s]%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class UpdateSecrets:
    def __init__(self, secrets_key, secrets_value, repo_name, github_token):
        self.secrets_key = secrets_key
        self.secrets_value = secrets_value
        self.repo_name = repo_name
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {github_token}'
        }

        self.public_key = self.get_public_key()
        self.encrypted_value = self.encrypt_secrets()
        self.upload_secrets()

    def get_public_key(self):
        logging.info('正在获取public_key')
        url = f'https://api.github.com/repos/{self.repo_name}/actions/secrets/public-key'
        response = requests.get(url=url, headers=self.headers)
        json_data = response.json()
        if 'key' in json_data:
            logging.info('获取public_key成功')
            return json_data
        else:
            raise RuntimeError(f'获取public_key失败：\n{json_data}')

    def encrypt_secrets(self):
        logging.info(f'正在加密{self.secrets_key}')
        public_key = public.PublicKey(self.public_key['key'].encode('utf-8'), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(self.secrets_value.encode('utf-8'))
        encrypted_value = b64encode(encrypted).decode('utf-8')
        logging.info(f'加密{self.secrets_key}成功')
        return encrypted_value

    def upload_secrets(self):
        logging.info(f'正在上传{self.secrets_key}')
        url = f'https://api.github.com/repos/{self.repo_name}/actions/secrets/{self.secrets_key}'
        data = {
            'encrypted_value': self.encrypted_value,
            'key_id': self.public_key['key_id']
        }
        response = requests.put(url=url, headers=self.headers, json=data)
        if response.status_code == 201:
            logging.info(f'新建{self.secrets_key}成功')
        elif response.status_code == 204:
            logging.info(f'上传{self.secrets_key}成功')
        else:
            raise RuntimeError(f'上传{self.secrets_key}失败：\n{response.json()}')
