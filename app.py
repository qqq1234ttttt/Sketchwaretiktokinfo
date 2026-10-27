import os
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

app = Flask(__name__, template_folder='.')

# နိုင်ငံကုဒ်များကို အမည်အပြည့်အစုံသို့ ပြောင်းပေးမည့် ဇယား
COUNTRY_MAP = {
    "MM": "Myanmar (Burma)",
    "US": "United States",
    "TH": "Thailand",
    "SG": "Singapore",
    "MY": "Malaysia",
    "ID": "Indonesia",
    "VN": "Vietnam",
    "PH": "Philippines",
    "CN": "China",
    "JP": "Japan",
    "KR": "South Korea",
    "GB": "United Kingdom",
    "IN": "India",
    "TW": "Taiwan"
}

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
        "Host": "www.tiktok.com",
        "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 8.0.0; Plume L2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Mobile Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(f'https://www.tiktok.com/@{username}', headers=headers)
        
        if response.status_code != 200:
            return None, f"Failed to retrieve data (Status: {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        user_data_script = None
        for script in soup.find_all('script'):
            if 'userInfo' in script.text:
                user_data_script = script.string
                break
        
        if not user_data_script:
            return None, "No user data found in the script."
        
        user_data_json = json.loads(user_data_script)
        user_info = user_data_json.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {}).get('userInfo', {})
        user = user_info.get('user', {})
        
        nickname = user.get('nickname', 'N/A')
        bio = user.get('signature', 'N/A')
        user_id = user.get('id', 'N/A')
        
        # Region ကို ရယူပြီး Country Code ကို အမည်အပြည့်အစုံသို့ ပြောင်းလဲခြင်း
        raw_region = user.get('region', '').strip().upper()
        if not raw_region or len(raw_region) > 3:
            # SEO data သို့မဟုတ် အခြားနေရာမှ ထပ်မံရှာဖွေရန်
            raw_region = user_data_json.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {}).get('seoProps', {}).get('seoData', {}).get('region', '').strip().upper()
        
        # ဇယားထဲမှာ ရှိရင် အမည်အပြည့်အစုံထုတ်ပေးမည်၊ မရှိရင် Original Code ကိုပဲ ပြမည်
        if raw_region in COUNTRY_MAP:
            region = COUNTRY_MAP[raw_region]
        elif raw_region:
            region = raw_region
        else:
            region = "GLOBAL / UNKNOWN"

        create_time_unix = user.get('createTime', 0)
        create_time = datetime.utcfromtimestamp(create_time_unix).strftime('%Y-%m-%d %H:%M:%S') if create_time_unix else 'N/A'
        
        stats = user_info.get('stats', {})
        followers = format_number(stats.get('followerCount', 0))
        following = format_number(stats.get('followingCount', 0))
        likes = format_number(stats.get('heartCount', 0))
        videos = format_number(stats.get('videoCount', 0))
        
        return {
            "username": username,
            "nickname": nickname,
            "bio": bio,
            "user_id": user_id,
            "region": region,
            "create_time": create_time,
            "followers": followers,
            "following": following,
            "likes": likes,
            "videos": videos
        }, None
        
    except json.JSONDecodeError as e:
        return None, f"JSON decoding error: {e}"
    except Exception as e:
        return None, f"Error: {e}"

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
