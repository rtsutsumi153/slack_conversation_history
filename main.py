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

    unique_messages = []

    for app_channel in app_channels:
        messages = utils.get_messages(app_channel["id"], app_channel["name"], users_dict)
        seen_texts = set()  # 出力済みのテキストを記憶するセットを初期化
        for msg in messages:
            if "bot_id" in msg: # botのメッセージは無視する
                continue
            else:
                user = users_dict[msg["user"]]

            text = msg["text"]
            thread_ts = msg.get("thread_ts", msg["ts"]) # スレッド場合はthread_tsを取得、それ以外はtsを取得
            if text not in seen_texts:  #テキストがセットに含まれていなければ出力し，セットに追加する
                unique_messages.append([app_channel["name"], user, text, thread_ts])
                seen_texts.add(text)

    df = pd.DataFrame(unique_messages, columns=["channel_name", "user", "text", "timestamp"])
    # 保存先ディレクトリを指定
    save_dir = "conversation_history"  # 例えば "C:/Users/YourName/Documents/output" など
    os.makedirs(save_dir, exist_ok=True)  # ディレクトリがなければ作成

    # 現在の日付を取得（例：2024-04-03)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"conversation_history_{date_str}.csv"

    # CSVの保存
    file_path = os.path.join(save_dir, file_name)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')