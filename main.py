import pandas as pd
import utils
import os
from datetime import datetime

if __name__ == "__main__":
    user_url = "users.list"
    users = utils.get_response(user_url)
    users_dict={}
    for user in users["members"]:
        users_dict[user["id"]] = user["name"]
    
    # すべてのチャンネルのうち，アプリが追加されているチャンネルのみを抽出して取得
    app_channels = utils.extract_app_channels()

    for app_channel in app_channels:
        unique_messages = []

        # 保存先ディレクトリを指定
        save_dir = "conversation_history"  # 例えば "C:/Users/YourName/Documents/output" など
        os.makedirs(save_dir, exist_ok=True)  # ディレクトリがなければ作成

        file_exist = utils.search_file_name(save_dir, app_channel["name"]) # save_dir内にapp_channel["name"]を含むファイル名のマイルが存在するか調べる

        #初めてのメッセージ履歴データの取得である場合（conversation_historyに指定したチャンネルのメッセージ履歴がまだない場合）は全てのメッセージ履歴を取得して新しく保存
        #2回目以降のメッセージ履歴取得である場合は差分のみ取得
        if  not file_exist:
            messages = utils.get_messages(app_channel["id"], app_channel["name"], users_dict)
        else:
            # 前回のメッセージ履歴データの最後のメッセージのタイムスタンプを取得
            oldest_ts = utils.get_oldest_message_ts(save_dir, app_channel["name"])
            
            # oldest_ts以降のメッセージのみを取得
            messages = utils.get_messages(app_channel["id"], app_channel["name"], users_dict, oldest_ts=oldest_ts)

        seen_texts = set()  # 出力済みのテキストを記憶するセットを初期化
        for msg in messages:
            if "bot_id" in msg: # botのメッセージは無視する
                continue
            else:
                user = users_dict[msg["user"]]

            text = msg["text"]
            ts = msg.get("ts") # メッセージのtsを取得
            thread_ts = msg.get("thread_ts", "not_thread") # スレッド内のメッセージならthread_tsにそのスレッドが立てられた時刻を記載．スレッドではないメッセージならnot_threadと記載．
            if text not in seen_texts:  #テキストがセットに含まれていなければ出力し，セットに追加する
                unique_messages.append([app_channel["name"], user, text, ts, thread_ts])
                seen_texts.add(text)
        
        df = pd.DataFrame(unique_messages, columns=["channel_name", "user", "text", "message_timestamp", "thread_timestamp"])

        # 現在の日付を取得（例：2024-04-03)
        #date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        #file_name = f"{app_channel["name"]}_{date_str}.csv"

        # CSVの保存
        #file_path = os.path.join(save_dir, file_name)
        #df.to_csv(file_path, index=False, encoding='utf-8-sig')

        # メッセージ履歴の差分を既存のcsvに追記
        utils.add_csv(save_dir, app_channel["name"], df, file_exist)
