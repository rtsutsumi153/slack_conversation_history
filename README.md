# slack_conversation_history
このプロジェクトはSlackの無料プランでは90日を経過したメッセージが閲覧できなくなるという問題に対処するため，SlackAPIを用いてメッセージ履歴を取得し外部メモリに保存することで，あとでメンバーが閲覧できるようにするアプリケーションです．
SlackAPIを用いて前回のメッセージ履歴取得から追加された部分のメッセージを取得してその差分をcsvファイルに追記するするようにしています．

##　セットアップ

### 前提条件
- Slackアプリケーションの作成

- Python >= 3.9.19

- pyenvに入る

- 各種モジュールのセットアップ
```bssh
pip install --upgrade pip
pip install -r requirements.txt
```

- `.env`ファイルにSlackAPIキーを入力
```bash
export SLACK_TOKEN='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

### メッセージを取得したいSlackのチャンネルに作成したアプリケーションを入れる
任意のチャンネルにアプリケーションを入れる．アプリケーションが入っているチャンネルは全てメッセージ履歴が取得される．

## メッセージ履歴を取得
- `main.py`を実行．
```bash
python main.py
```

- `conversation_history`フォルダに`[チャンネル名]_20250405_121946.csv`などの名前でメッセージ履歴が保存される．
- メッセージ履歴を更新したい場合は再度`main.py`を実行すれば，前回のメッセージ取得からの差分のみがcsvファイルに追記される．
```bash
python main.py
```