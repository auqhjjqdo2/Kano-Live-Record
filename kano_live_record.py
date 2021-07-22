import json
import logging
import os
import random
import re
import time
from threading import Thread

from jsonpath import jsonpath
import requests

from set_refresh_token import set_onedrive_auth


class KanoLiveRecord:
    def __init__(self, live_type, name, user_id):
        self.headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        self.live_type = live_type
        self.msg = f'[{self.live_type}][{name}]'
        self.user_id = user_id
        self.recording = []
        self.run()

    def run(self):
        logging.info(f'{self.msg}正在检测直播状态')
        while True:
            try:
                live_info = self.live_status()
                if live_info:
                    for item in live_info:
                        Thread(target=self.live_record, args=(item,)).start()
            except Exception as error:
                logging.exception(error)
                send_qsmg(error)
            time.sleep(random.randint(5, 15))

    def get_bilibili_live(self):
        url = f'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={self.user_id}'
        response = requests.get(url=url, headers=self.headers)
        if response.ok:
            json_data = response.json()
            return json_data
        else:
            raise RuntimeError(f'{self.msg}检测直播流失败\n{response}')

    def get_youtube_live(self):
        url = 'https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
        data = {
            "context": {
                "client": {
                    "hl": "zh-CN",
                    "clientName": "WEB",
                    "clientVersion": "2.20210526.07.00",
                    "timeZone": "Asia/Shanghai"
                },
            },
            "browseId": self.user_id,
            "params": "EgZ2aWRlb3MgOQ%3D%3D"
        }
        response = requests.post(url=url, headers=self.headers, json=data)
        if response.ok:
            json_data = response.json()
            return json_data
        else:
            raise RuntimeError(f'{self.msg}检测直播流失败\n{response}')

    def get_youtube_info(self, video_id):
        url = 'https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
        data = {
            "context": {
                "client": {
                    "hl": "zh-CN",
                    "clientName": "WEB",
                    "clientVersion": "2.20210701.07.00",
                    "timeZone": "Asia/Shanghai"
                },
            },
            "videoId": video_id
        }
        response = requests.post(url=url, headers=self.headers, json=data)
        if response.ok:
            json_data = response.json()
            return json_data
        else:
            raise RuntimeError(f'{self.msg}检测直播流失败\n{response}')

    def get_twitch_live(self):
        url = f'https://api.twitch.tv/helix/streams?user_id={self.user_id}'
        headers = json.loads(os.getenv('TWITCH_HEADERS'))
        response = requests.get(url=url, headers=headers)
        if response.ok:
            json_data = response.json()
            return json_data
        else:
            raise RuntimeError(f'{self.msg}检测直播流失败\n{response}')

    def live_status(self):
        live_info = []
        if self.live_type == 'bilibili':
            json_data = self.get_bilibili_live()
            live_status = json_data['data']['live_status']
            if live_status == 1:
                live_url = f'https://live.bilibili.com/{self.user_id}'
                if live_url not in self.recording:
                    live_title = json_data['data']['title']
                    start_time = json_data['data']['live_time']
                    live_time = time.strftime('%Y.%m.%d', time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
                    show_msg(f'{self.msg}检测到直播流\n{live_title}\n{live_url}')
                    live_info.append({
                        'live_title': live_title,
                        'live_url': live_url,
                        'live_time': live_time
                    })
        elif self.live_type == 'youtube':
            json_data = self.get_youtube_live()
            video_id_list = jsonpath(json_data, "$.contents..[?(@.title.runs.0.text=='正在直播')]..[?(@.title)].videoId")
            if video_id_list:
                for video_id in video_id_list:
                    video_info = self.get_youtube_info(video_id)
                    if 'isLive' in video_info['videoDetails']:
                        live_url = f'https://www.youtube.com/watch?v={video_id}'
                        if live_url not in self.recording:
                            live_title = video_info['videoDetails']['title']
                            start_time = video_info['microformat']['playerMicroformatRenderer']['liveBroadcastDetails']['startTimestamp']
                            live_time = time.strftime('%Y.%m.%d', time.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z'))
                            show_msg(f'{self.msg}检测到直播流\n{live_title}\n{live_url}')
                            live_info.append({
                                'live_title': live_title,
                                'live_url': live_url,
                                'live_time': live_time
                            })
        elif self.live_type == 'twitch':
            json_data = self.get_twitch_live()
            if json_data['data']:
                data = json_data['data'][0]
                live_url = f"https://www.twitch.tv/{data['user_login']}"
                if live_url not in self.recording:
                    live_title = data['title']
                    start_time = data['started_at']
                    live_time = time.strftime('%Y.%m.%d', time.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ'))
                    show_msg(f'{self.msg}检测到直播流\n{live_title}\n{live_url}')
                    live_info.append({
                        'live_title': live_title,
                        'live_url': live_url,
                        'live_time': live_time
                    })
        return live_info

    def live_record(self, live_info):
        live_title = live_info['live_title']
        live_url = live_info['live_url']
        live_time = live_info['live_time']

        show_msg(f'{self.msg}开始录制直播\n{live_title}')
        self.recording.append(live_url)
        timestamp = str(time.time()).replace('.', '')
        os.system(f'streamlink "{live_url}" best -o "{timestamp}" | tee Streamlink_{timestamp}.txt')

        with open(f'Streamlink_{timestamp}.txt', 'r', encoding='utf-8') as f:
            record_result = f.read()
        if 'ended' in record_result:
            show_msg(f'{self.msg}直播录制结束\n{live_title}')
        else:
            error = f"{self.msg}直播录制失败\n{live_title}\n{re.findall(r'error:(.*)', record_result)[0]}"
            logging.error(error)
            send_qsmg(error)

        os.system(f'ffmpeg -i "{timestamp}" -c copy "{timestamp}.mp4"')
        show_msg(f'{self.msg}ffmpeg转码完成\n{live_title}')
        Thread(target=self.file_upload, args=(timestamp, live_title, live_time)).start()
        self.recording.remove(live_url)

    def file_upload(self, timestamp, live_title, live_time):
        for i in '"*:<>?/\|':
            live_title = live_title.replace(i, ' ')
        save_name = f'[{timestamp}][{live_time}][{self.live_type}]{live_title}'
        show_msg(f'{self.msg}开始上传到OneDrive\n{live_title}')
        os.system(f'./OneDriveUploader -f -s "{timestamp}.mp4" -r "/鹿乃/直播录屏" -n "{save_name}.mp4" | tee OneDriveUploader_{timestamp}.txt')
        with open(f'OneDriveUploader_{timestamp}.txt', 'r', encoding='utf-8') as f:
            upload_result = f.read()
        if '100%' in upload_result:
            show_msg(f'{self.msg}上传到OneDrive成功\n{live_title}')
        else:
            error = f'{self.msg}上传到OneDrive失败\n{live_title}'
            logging.error(error)
            send_qsmg(error)


def show_msg(msg):
    logging.info(msg)
    send_qsmg(msg)


def send_qsmg(msg):
    qsmg_token = os.getenv('QSMG_TOKEN')
    qmsg_url = f'https://qmsg.zendee.cn/send/{qsmg_token}'
    qmsg_data = {'msg': msg}
    try:
        requests.post(url=qmsg_url, data=qmsg_data)
    except:
        logging.exception('Qmsg酱发送消息失败')


def run():
    set_onedrive_auth()
    data = {
        'bilibili': {
            '鹿乃': '15152878'
        },
        'youtube': {
            '斑比鹿乃': 'UCShXNLMXCfstmWKH_q86B8w',
            '魔法鹿乃': 'UCfuz6xYbYFGsWWBi3SpJI1w'
        },
        'twitch': {
            '魔法鹿乃': '704557048'
        }
    }
    for live_type, values in data.items():
        for name, user_id in values.items():
            Thread(target=KanoLiveRecord, args=(live_type, name, user_id)).start()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s]%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    run()
    # Thread(target=KanoLiveRecord, args=('bilibili', '24小时云自习室', '21179176')).start()
    # Thread(target=KanoLiveRecord, args=('youtube', 'Lofi Girl', 'UCSJ4gkVC6NrvII8umztf0Ow')).start()
