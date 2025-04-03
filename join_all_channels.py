import requests
import time
from dotenv import load_dotenv
import os

# .envファイルから環境変数を読み込む
load_dotenv()
#SpotifyAPIのアクセストークン情報
# 環境変数からSpotify APIのクライアントIDとシークレットを取得
slack_token = os.getenv('SLACK_TOKEN')

def get_public_channels():
    """ワークスペース内の全パブリックチャンネルを取得する関数"""
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Beerer {slack_token}"}
    params = {"types": "public_channel", "limit": 1000}

    all_channels =[]
    cursor = None

    while True:
        if cursor:
            params["cursor"] = cursor

        response = requests.get(url, headers=headers, params=params).json()

        if not response.get("ok"):
            print("Error:", response.get("error"))
            return []
        
        all_channels.extend(response["channels"])
        cursor = response.get("response_metadata", {}).get("next_cursor")

        if not cursor:
            break

        time.sleep(1)  # API制限回避

        return all_channels


def join_channel(channel_id):
    """指定したチャンネルにボットを追加する関数"""
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Beerer {slack_token}"}
    params = {"channel": channel_id}

    response = requests.post(url, headers=headers, params=params).json()

    if response.get("ok"):
        print(f"ボットが {channel_id} に参加しました！")
    else:
        print(f"エラー: {response.get('error')}")


# すべてのチャンネルにボットを参加させる
channels = get_public_channels()
for channel in channels:
    join_channel(channel["id"])     

