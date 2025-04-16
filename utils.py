import requests
from tqdm import tqdm
from dotenv import load_dotenv
import os
import csv
from collections import deque
import pandas as pd
from datetime import datetime
import re

# .envファイルから環境変数を読み込む
load_dotenv()
#SpotifyAPIのアクセストークン情報
# 環境変数からSpotify APIのクライアントIDとシークレットを取得
slack_token = os.getenv('SLACK_TOKEN')

def get_response(api_url, payload=None):
    """SlackAPIにリクエストを送ってレスポンスをもらう関数
    Args:
        api_url (str): BASE_URL以下に記載する,使用するSlackAPIの関数の名前.
        payload (dic): リクエストに付加するSlackAPIの関数のパラメータ

    Returns:
        res.json(): SlackAPIからのレスポンスのjson
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
    '''ワークスペースの全てのチャンネルの情報を取得する関数
    
    Returns:
        channels (dic):  ワークスペースの全てのチャンネルの情報
    '''
    api_url = "conversations.list"
    #payload = {"types": "public_channel,private_channel"}
    channels = get_response(api_url)

    return channels

def extract_app_channels():
    '''すべてのチャンネルのうち，アプリが追加されているチャンネルのみを抽出する関数
    Returns:
        app_channels (dic): アプリが追加されているチャンネル
    '''
    # すべてのチャンネルを取得
    channels = get_channels()
    # すべてのチャンネルのうち，アプリが追加されているチャンネルのみを抽出
    app_channels = []
    for channel in channels["channels"]:
        if channel["is_member"]:
            app_channels.append(channel)
    
    return app_channels

    
def get_messages(channel_id, channel_name, users_dict, oldest_ts=0):
    '''指定したチャンネルのメッセージ履歴を取得する関数
    Args:
        channel_id (str): チャンネルのID
        channel_name (str): チャンネルの名前
        users_dict (dic): ワークスペース内の全てのユーザ情報
        oldest_ts (str): 前回のメッセージ履歴取得ファイルの一番最後のメッセージのタイムスタンプ

    Returns:
        messages_sorted: 取得したメッセージ情報をメッセージのタイムスタンプ順でソートしたもの
    '''
    api_url = "conversations.history"
    payload = {
        "channel": channel_id,
        "limit": 1000,
        "oldest": oldest_ts,
        }

    message_logs = get_response(api_url, payload=payload)

    messages = []

    for item in tqdm(message_logs["messages"]):
        messages.append(item)
        
        # もしitemがスレッドの親メッセージだったら，そのスレッド内のメッセージも取得する．
        if "thread_ts" in item:
            thread_ts = item["thread_ts"]
            reply_api_url = "conversations.replies"
            payload = {
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 1000
                }
            replies = get_response(reply_api_url, payload=payload)

            # 最初の親メッセージを除外してスレッド内のメッセージを追加する
            for reply in replies["messages"]:
                if reply.get("thread_ts") == thread_ts and reply.get("parent_user_id") is not None:
                    messages.append(reply)
    
    # メッセージの送信時間順で並び替え
    messages_sorted = sorted(messages, key=lambda x: x["ts"])
    return messages_sorted

def get_oldest_message_ts(save_dir, channel_name):
    '''前回のメッセージ履歴データの最後のメッセージのタイムスタンプを取得
    Args:
        save_dir (str): メッセージ履歴データを保存しているディレクトリのパス
        channel_name (str): メッセージ履歴を取得したいチャンネルの名前
    
    Returns:
        last_row[3]: 前回のメッセージ履歴データの最後のメッセージのタイムスタンプ
    '''
    leatest_file = get_latest_file(save_dir, channel_name) # 最も新しいメッセージ履歴のファイル名を検索
    latest_file_path = f"{save_dir}/{leatest_file}"

    with open(latest_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        last_row = deque(reader, maxlen=1)[0] # 最後の１行だけ取得
    
    # もし最後のメッセージがスレッドの親メッセージまたはスレッド内のメッセージだったら，親メッセージのタイムスタンプを返す．スレッドではなかったら，そのメッセージのタイムスタンプを返す．
    #if last_row[4] == "not_thread":
    #    return last_row[3] # message_timestampを返す
    #else:
    #    return last_row[4] # thread_timestampを返す

    return last_row[3]  # message_timestampを返す

def add_csv(save_dir, channel_name, df):
    '''前回のメッセージ取得履歴のファイルに現在のメッセージの差分を追記する関数
    Args:
        save_dir (str): メッセージ履歴データを保存しているディレクトリのパス
        channel_name (str): メッセージ履歴を取得したいチャンネルの名前
        df (PandasライブラリのDataFrameクラスのインスタンス): 前回のメッセージ取得履歴のファイルからの現在のメッセージの差分
    '''
    # 追記先のファイル（既存のCSV）
    leatest_file = get_latest_file(save_dir, channel_name) # 前回のメッセージ取得履歴のファイル名を検索
    target_csv = f"{save_dir}/{leatest_file}"

    # 追記（ヘッダーなしで追記モード）
    df.to_csv(target_csv, mode='a', header=False, index=False)

    # ファイルの名前に更新日を記載
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    renamed_csv = f"{save_dir}/{channel_name}_{date_str}.csv"
    os.rename(target_csv, renamed_csv)

def get_latest_file(save_dir, channel_name):
    '''これまで記録されているメッセージ履歴の中で最も新しいファイルのファイル名を検索する関数
    Args:
        save_dir (str): メッセージ履歴データを保存しているディレクトリのパス
        channel_name (str): メッセージ履歴を取得したいチャンネルの名前
    
    Returns:
        latest_file: save_dir内のメッセージ履歴データのcsvファイルの中でファイル名に記載されている記録日時が最も新しいもののファイル名
    '''
    # 変数を正規表現に埋め込む（チャンネル名をエスケープして安全に）
    escaped_channel_name = re.escape(channel_name)
    pattern = re.compile(rf'^{escaped_channel_name}_(\d{{8}}_\d{{6}})\.csv$')  #フォーマット channel_name_YYYYMMDD_HHMMSS.csv

    latest_file = None
    latest_date = None

    for filename in os.listdir(save_dir):
        match = pattern.search(filename)
        if match:
            file_date = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
            if latest_date is None or file_date > latest_date:
                latest_date = file_date
                latest_file = filename

    return latest_file

def remove_first_element(messages):
    '''messagesの先頭の要素を削除して詰める関数

    '''
    if messages:
        return messages[1:]
    else:
        return messages

def print_channel_messages(channel_name, messages, users_dict):
    seen_texts = set() # 出力済みのテキストを記憶するセットを初期化
    for msg in messages:
        user = users_dict[msg["user"]]
        text = msg["text"]
        thread_ts = msg.get("thread_ts", msg["ts"]) # スレッドの場合はthread_tsを取得，それ以外はtsを取得
        if text not in seen_texts: # テキストがセットに含まれていなければ出力し，セットに追加する
            print(f"{channel_name},{user},{text},{thread_ts}")
            seen_texts.add(text)