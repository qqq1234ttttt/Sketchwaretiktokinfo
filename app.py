import os
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# template_folder='.' ထည့်ထားတာကြောင့် Folder ဆောက်စရာမလိုတော့ပါဘူး
app = Flask(__name__, template_folder='.')

def format_number(value):
    try:
        value = float(value)
        if value >= 1000000:
            return f"{value / 1000000:.1f}m"
        elif value >= 1000:
            return f"{value / 1000:.1f}k"
        return str(int(value))
    except:
        return "0"

def get_tiktok_data(username):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(f'https://www.tiktok.com/@{username}', headers=headers)
        if response.status_code != 200:
            return None, "Data ဆွဲထုတ်၍ မရပါ။ (Username မှန်မမှန် စစ်ပါ)"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        user_data_script = None
        for script in soup.find_all('script'):
            if 'userInfo' in script.text:
                user_data_script = script.string
                break
        
        if not user_data_script:
            return None, "User ဒေတာ ရှာမတွေ့ပါ။"
        
        user_data_json = json.loads(user_data_script)
        user_info = user_data_json.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {}).get('userInfo', {})
        user = user_info.get('user', {})
        
        create_time_unix = user.get('createTime', 0)
        create_time = datetime.utcfromtimestamp(create_time_unix).strftime('%Y-%m-%d') if create_time_unix else 'N/A'
        
        stats = user_info.get('stats', {})
        
        return {
            "username": username,
            "nickname": user.get('nickname', 'N/A'),
            "bio": user.get('signature', 'N/A'),
            "region": user.get('region', 'N/A'),
            "create_time": create_time,
            "followers": format_number(stats.get('followerCount', 0)),
            "following": format_number(stats.get('followingCount', 0)),
            "likes": format_number(stats.get('heartCount', 0)),
            "videos": format_number(stats.get('videoCount', 0))
        }, None
    except Exception as e:
        return None, f"Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    data = None
    error = None
    if request.method == 'POST':
        username = request.form.get('username').strip().replace('@', '')
        data, error = get_tiktok_data(username)
    return render_template('index.html', data=data, error=error)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
