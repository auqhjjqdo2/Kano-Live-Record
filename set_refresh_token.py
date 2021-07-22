import json
import os

from update_secrets import *


def get_refresh_token():
    logging.info('正在获取refresh_token')
    url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': os.getenv('ONEDRIVE_REFRESH_TOKEN'),
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET')
    }
    response = requests.post(url=url, data=data)
    json_data = response.json()
    if 'refresh_token' in json_data:
        logging.info('获取refresh_token成功')
        return json_data['refresh_token']
    else:
        raise RuntimeError(f'获取refresh_token失败：\n{json_data}')


def set_onedrive_auth():
    logging.info('正在初始化OneDriveUploader授权')
    onedrive_refresh_token = os.getenv('ONEDRIVE_REFRESH_TOKEN')
    if '0.A' in onedrive_refresh_token:
        onedrive_auth = {
            'RefreshToken': onedrive_refresh_token,
            'RefreshInterval': 1500,
            'ThreadNum': '8',
            'BlockSize': '2',
            'SigleFile': '100',
            'MainLand': False,
            'MSAccount': False
        }
        with open('auth.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(onedrive_auth))
        logging.info('写入ONEDRIVE_REFRESH_TOKEN成功')
    else:
        raise RuntimeError('写入ONEDRIVE_REFRESH_TOKEN失败')


if __name__ == '__main__':
    refresh_token = get_refresh_token()
    repo_name = os.getenv('REPO_NAME')
    github_token = os.getenv('GH_TOKEN')
    UpdateSecrets('ONEDRIVE_REFRESH_TOKEN', refresh_token, repo_name, github_token)
