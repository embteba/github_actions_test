#!/usr/bin/env python3
"""
最新のコミットメッセージをリモートのREADME.mdに書き込むスクリプト
GitHub APIを使用してリモートリポジトリのREADMEを更新する
"""

import subprocess
import os
import base64
import json
from pathlib import Path
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


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
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"エラー: git log コマンドが失敗しました: {e}")
        return None


def get_github_context():
    """
    GitHub Actionsの環境変数からリポジトリ情報を取得する
    
    Returns:
        dict: owner, repo, token を含む辞書
    """
    owner = os.getenv('GITHUB_REPOSITORY_OWNER')
    repo = os.getenv('GITHUB_REPOSITORY', '').split('/')[-1]
    token = os.getenv('GITHUB_TOKEN')
    
    if not all([owner, repo, token]):
        raise ValueError(
            "GitHub環境変数が設定されていません。"
            "GITHUB_REPOSITORY_OWNER, GITHUB_REPOSITORY, GITHUB_TOKEN が必須です。"
        )
    
    return {'owner': owner, 'repo': repo, 'token': token}


def get_readme_from_github(owner, repo, token):
    """
    GitHubからREADME.mdを取得する
    
    Args:
        owner (str): リポジトリオーナー
        repo (str): リポジトリ名
        token (str): GitHubトークン
    
    Returns:
        tuple: (content, sha) - 現在の内容とコミットSHA
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.raw',
        'User-Agent': 'GitHub-Actions-Script'
    }
    
    try:
        req = Request(url, headers=headers)
        response = urlopen(req)
        content = response.read().decode('utf-8')
        
        # SHAも取得する（更新時に必要）
        url_json = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
        headers['Accept'] = 'application/vnd.github.v3+json'
        req_json = Request(url_json, headers=headers)
        response_json = urlopen(req_json)
        data = json.loads(response_json.read().decode('utf-8'))
        
        return content, data.get('sha')
    except URLError as e:
        print(f"エラー: GitHubからREADME.mdを取得できませんでした: {e}")
        return None, None


def update_readme_on_github(owner, repo, token, content, message, sha):
    """
    GitHubのREADME.mdを更新する
    
    Args:
        owner (str): リポジトリオーナー
        repo (str): リポジトリ名
        token (str): GitHubトークン
        content (str): 新しいコンテンツ
        message (str): コミットメッセージ
        sha (str): 更新前のファイルSHA
    
    Returns:
        bool: 成功時True
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
    
    # コンテンツをBase64エンコード
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    payload = {
        'message': message,
        'content': encoded_content,
        'sha': sha
    }
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-Actions-Script',
        'Content-Type': 'application/json'
    }
    
    try:
        req = Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='PUT'
        )
        response = urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        return True
    except URLError as e:
        print(f"エラー: GitHubでREADME.mdを更新できませんでした: {e}")
        return False


def main():
    """
    メイン処理
    1. 最新のコミットメッセージを取得
    2. GitHubからREADME.mdを取得
    3. コミットメッセージを追記
    4. GitHubに更新内容をコミット
    """
    try:
        # 最新のコミットメッセージを取得
        commit_message = get_latest_commit_message()
        if not commit_message:
            print("エラー: コミットメッセージを取得できませんでした。")
            return 1
        
        # GitHub コンテキストを取得
        context = get_github_context()
        print(f"✓ GitHub: {context['owner']}/{context['repo']}")
        
        # GitHubからREADME.mdを取得
        content, sha = get_readme_from_github(
            context['owner'],
            context['repo'],
            context['token']
        )
        
        if content is None:
            print("エラー: README.mdを取得できませんでした。")
            return 1
        
        # タイムスタンプ付きでコミットメッセージを追加
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"\n[{timestamp}] {commit_message}"
        new_content = content + entry
        
        # GitHubのREADME.mdを更新
        update_message = f"Update README: {commit_message[:50]}"
        success = update_readme_on_github(
            context['owner'],
            context['repo'],
            context['token'],
            new_content,
            update_message,
            sha
        )
        
        if success:
            print(f"✓ リモートのREADME.mdを更新しました")
            print(f"  {entry}")
            return 0
        else:
            print("エラー: README.mdの更新に失敗しました。")
            return 1
    
    except ValueError as e:
        print(f"エラー: {e}")
        return 1
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
