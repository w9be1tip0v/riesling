import requests
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
import time

# .envファイルを読み込む
load_dotenv()

# APIキーを取得
api_key = os.getenv('API_KEY')

# 初期URLとパラメータを設定
base_url = 'https://api.polygon.io/v3/reference/splits'
params = {
    'apiKey': api_key,
    'limit': 1000  
}

# 全データを格納するリストを初期化
all_splits = []

while True:
    try:
        # データを取得
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # データを全データリストに追加
        splits = data.get('results', [])
        all_splits.extend(splits)

        # next_urlを取得し、次のリクエスト用のパラメータを更新
        next_url = data.get('next_url', None)
        if next_url:
            # next_urlからcursorを抽出
            cursor = next_url.split('cursor=')[1]
            params['cursor'] = cursor
        else:
            break

        # 1分間に5リクエストに収めるため13秒待機
        time.sleep(13)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        break

# 必要なカラムを抽出し、adj_factorを計算
formatted_splits = []
for split in all_splits:
    formatted_splits.append({
        'ticker': split['ticker'],
        'execution_date': split['execution_date'],
        'split_from': split['split_from'],
        'split_to': split['split_to'],
        'adj_factor': split['split_from'] / split['split_to']
    })

# DataFrameに変換
df = pd.DataFrame(formatted_splits)

# タイムスタンプを取得
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# 出力ディレクトリを設定
output_dir = 'csv'
os.makedirs(output_dir, exist_ok=True)

# 出力ファイル名を設定
csv_file = os.path.join(output_dir, f'polygon_splits_data_{timestamp}.csv')

# データをCSVファイルに出力
df.to_csv(csv_file, index=False)

print(f'Data has been written to {csv_file}')
