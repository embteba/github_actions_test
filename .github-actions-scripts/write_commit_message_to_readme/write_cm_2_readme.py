#!/usr/bin/env python3
"""
最新のコミットメッセージをREADME.mdに書き込むスクリプト
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime


def get_latest_commit_message():
    """
    最新のコミットメッセージを取得する
    
    Returns:
        str: 最新のコミットメッセージ
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"エラー: git log コマンドが失敗しました: {e}")
        return None


def get_readme_path():
    """
    README.mdのパスを取得する
    スクリプトはリポジトリのルートを基準とする
    
    Returns:
        Path: README.mdのパス
    """
    # リポジトリルートを取得
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        repo_root = Path(result.stdout.strip())
        return repo_root / 'README.md'
    except subprocess.CalledProcessError:
        # git コマンドが失敗した場合、スクリプトからの相対パスで探す
        script_dir = Path(__file__).parent
        return script_dir.parent.parent / 'README.md'


def write_commit_message_to_readme(commit_message):
    """
    コミットメッセージをREADME.mdに追記する
    
    Args:
        commit_message (str): 書き込むコミットメッセージ
    """
    readme_path = get_readme_path()
    
    # README.mdが存在しない場合は作成
    if not readme_path.exists():
        print(f"警告: {readme_path} が見つかりません。新規作成します。")
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.touch()
    
    # 現在のREADME.mdを読み込む
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # タイムスタンプ付きでコミットメッセージを追加
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n[{timestamp}] {commit_message}"
    
    # README.mdに追記
    with open(readme_path, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    print(f"✓ README.md に以下のメッセージを追記しました:")
    print(f"  {entry}")


def main():
    """
    メイン処理
    """
    # 最新のコミットメッセージを取得
    commit_message = get_latest_commit_message()
    
    if not commit_message:
        print("エラー: コミットメッセージを取得できませんでした。")
        return 1
    
    # README.mdに書き込む
    write_commit_message_to_readme(commit_message)
    
    return 0


if __name__ == '__main__':
    exit(main())
