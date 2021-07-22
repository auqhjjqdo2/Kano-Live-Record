import asyncio
import datetime
import os
import re

import requests

from set_refresh_token import set_onedrive_auth


async def run():
    set_onedrive_auth()
    link_list = os.getenv('KANO_YOUTUBE_LINK').split()
    task_list = [asyncio.create_task(transfer(link)) for link in link_list]
    for task in task_list:
        await task


def get_video_data(video_id):
    data = {
        "context": {
            "client": {
                "hl": "zh-CN",
                "clientName": "WEB",
                "clientVersion": "2.20210526.07.00",
                "timeZone": "Asia/Shanghai"
            },
        },
        "videoId": video_id
    }
    json_data = requests.post(url='https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8', json=data).json()
    return json_data


async def transfer(link):
    video_id = re.findall(r'watch\?v=(.*)', link)[0]
    video_data = get_video_data(video_id)
    title = video_data['videoDetails']['title']
    for i in '"*:<>?/\|':
        title = title.replace(i, ' ')
    microformat = video_data['microformat']['playerMicroformatRenderer']
    if 'liveBroadcastDetails' in microformat:
        start_utc_time = datetime.datetime.strptime(microformat['liveBroadcastDetails']['startTimestamp'], '%Y-%m-%dT%H:%M:%S%z')
        date = (start_utc_time + datetime.timedelta(hours=8)).strftime('%Y.%m.%d')
    else:
        date = microformat['publishDate'].replace('-', '.')
    filename = f'[{date}][youtube]{title}.mp4'
    os.system(f'youtube-dl -f bestvideo+bestaudio --merge-output-format mp4 "{link}"')
    for name in os.listdir():
        if video_id in name:
            os.rename(name, filename)
            os.system(f'./OneDriveUploader -f -s "{filename}" -r "/鹿乃/直播录屏"')


if __name__ == '__main__':
    asyncio.run(run())
