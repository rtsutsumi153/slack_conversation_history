import requests
from tqdm import tqdm
from dotenv import load_dotenv
import os

# .envファイルから環境変数を読み込む
load_dotenv()
#SpotifyAPIのアクセストークン情報
# 環境変数からSpotify APIのクライアントIDとシークレットを取得
slack_token = os.getenv('SLACK_TOKEN')

def get_response(api_url, payload=None):
    """slackAPIにリクエストを送ってレスポンスをもらう関数
    """
    BASE_URL = "https://slack.com/api/"
    headers = {"Authorization": "Bearer {}".format(slack_token)}

    url = BASE_URL + api_url

    if payload:
        res = requests.get(url, headers=headers, params=payload)
        return res.json()
    else:
        res = requests.get(url, headers=headers)
        return res.json()
    
def get_channels():
    api_url = "conversations.list"
    #payload = {"types": "public_channel,private_channel"}
    channels = get_response(api_url)

    return channels

def extract_app_channels():
    # すべてのチャンネルを取得
    channels = get_channels()
    # すべてのチャンネルのうち，アプリが追加されているチャンネルのみを抽出
    app_channels = []
    for channel in channels["channels"]:
        if channel["is_member"]:
            app_channels.append(channel)
    
    return app_channels

    
def get_messages(channel_id, channel_name, users_dict):
    api_url = "conversations.history"
    payload = {
        "channel": channel_id,
        "limit": 1000
        }

    message_logs = get_response(api_url, payload=payload)

    messages = []

    for item in tqdm(message_logs["messages"]):
        messages.append(item)

        if "thread_ts" in item:
            thread_ts = item["thread_ts"]
            reply_api_url = "conversations.replies"
            payload = {
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 1000
                }
            replies = get_response(reply_api_url, payload=payload)

            # 最初のメッセージを除外してスレッド内のメッセージを追加する
            for reply in replies["messages"]:
                if reply.get("thread_ts") == thread_ts and reply.get("parent_user_id") is not None:
                    messages.append(reply)

    messages_sorted = sorted(messages, key=lambda x: x["ts"])
    return messages_sorted

def print_channel_messages(channel_name, messages, users_dict):
    seen_texts = set() # 出力済みのテキストを記憶するセットを初期化
    for msg in messages:
        user = users_dict[msg["user"]]
        text = msg["text"]
        thread_ts =msg.get("thread_ts", msg["ts"]) # スレッドの場合はthread_tsを取得，それ以外はtsを取得
        if text not in seen_texts: # テキストがセットに含まれていなければ出力し，セットに追加する
            print(f"{channel_name},{user},{text},{thread_ts}")
            seen_texts.add(text)