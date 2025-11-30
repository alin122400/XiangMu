import difflib
import requests
import re
from datetime import datetime, timedelta

# ===============================
# 城市库（可扩展）
# ===============================
CITY_MAP = {
    "beijing": "Beijing", "bj": "Beijing", "北京": "Beijing",
    "shanghai": "Shanghai", "sh": "Shanghai", "上海": "Shanghai",
    "guangzhou": "Guangzhou", "gz": "Guangzhou", "广州": "Guangzhou",
    "shenzhen": "Shenzhen", "sz": "Shenzhen", "深圳": "Shenzhen",
    "hangzhou": "Hangzhou", "hz": "Hangzhou", "杭州": "Hangzhou",
    "chengdu": "Chengdu", "成都": "Chengdu",
    "wuhan": "Wuhan", "武汉": "Wuhan",
}

CITY_COORDS = {
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Guangzhou": (23.1291, 113.2644),
    "Shenzhen": (22.5431, 114.0579),
    "Hangzhou": (30.2741, 120.1551),
    "Chengdu": (30.5728, 104.0668),
    "Wuhan": (30.5928, 114.3055),
}

# ===============================
# 天气代码 → 中文描述
# ===============================
WEATHER_DESC = {
    0: "晴",
    1: "基本晴",
    2: "多云",
    3: "阴",

    45: "有雾",
    48: "霜雾",

    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",

    61: "小雨",
    63: "中雨",
    65: "大雨",

    66: "冻雨",
    67: "冻雨",

    71: "小雪",
    73: "中雪",
    75: "大雪",

    77: "雪粒",

    80: "小阵雨",
    81: "中阵雨",
    82: "大阵雨",

    95: "雷雨",
    96: "雷雨并伴有冰雹",
    99: "强雷雨并伴有冰雹",
}

def wcode_to_text(code):
    return WEATHER_DESC.get(code, "天气状况不明")

# ===============================
# 模糊匹配城市
# ===============================
def fuzzy_city(text: str):
    text = text.lower()
    keys = list(CITY_MAP.keys())
    match = difflib.get_close_matches(text, keys, n=1, cutoff=0.3)
    return CITY_MAP[match[0]] if match else None

def extract_city(sentence):
    for key in CITY_MAP.keys():
        if key in sentence.lower():
            return CITY_MAP[key]
    words = re.findall(r"[a-zA-Z\u4e00-\u9fa5]+", sentence)
    for w in words:
        c = fuzzy_city(w)
        if c:
            return c
    return None

# ===============================
# 时间解析（今天/明天/后天）
# ===============================
def extract_date(sentence):
    now = datetime.now()

    if "后天" in sentence:
        return now + timedelta(days=2)
    if "明天" in sentence:
        return now + timedelta(days=1)
    if "今天" in sentence or "现在" in sentence:
        return now

    return now

# ===============================
# 查询天气
# ===============================
def get_forecast(city: str):
    lat, lon = CITY_COORDS[city]

    url = f"https://api.open-meteo.com/v1/forecast?" \
          f"latitude={lat}&longitude={lon}" \
          f"&hourly=temperature_2m,weathercode,windspeed_10m" \
          f"&timezone=Asia/Shanghai"

    try:
        return requests.get(url).json()
    except:
        return None

# ===============================
# 自然语言语义判断（优化版）
# ===============================
def interpret(user_text, temp, wcode, wind):
    weather_text = wcode_to_text(wcode)

    # 冷/热判断
    if "冷" in user_text:
        if temp < 12:
            return f"会有点冷，现在{weather_text}，气温约 {temp}°C。"
        else:
            return f"不会太冷，现在是{weather_text}，气温 {temp}°C。"

    if "热" in user_text:
        if temp >= 30:
            return f"会比较热，现在{weather_text}，气温 {temp}°C。"
        else:
            return f"不会太热，现在{weather_text}，气温只有 {temp}°C。"

    # 下雨判断
    if "雨" in user_text or "下不" in user_text:
        if weather_text in ["小雨","中雨","大雨","小阵雨","中阵雨","大阵雨","小毛毛雨","中毛毛雨","大毛毛雨"]:
            return f"预计有{weather_text}，建议带伞。"
        else:
            return f"不会下雨，现在是{weather_text}。"

    # 风判断
    if "风" in user_text:
        if wind > 25:
            return f"风挺大，风速约 {wind} km/h，天气是{weather_text}。"
        else:
            return f"风不大，风速 {wind} km/h，目前是{weather_text}。"

    # 默认返回
    return f"当前天气：{weather_text}，气温 {temp}°C，风速 {wind} km/h。"

# ===============================
# 主逻辑
# ===============================
def chat_weather(sentence):
    city = extract_city(sentence)
    if not city:
        return "我没有识别到你要查询的城市。"

    date = extract_date(sentence)

    data = get_forecast(city)
    if not data:
        return "天气服务目前不可用。"

    hourly = data["hourly"]
    temps = hourly["temperature_2m"]
    winds = hourly["windspeed_10m"]
    codes = hourly["weathercode"]

    idx = (date - datetime.now()).days * 24
    idx = max(0, min(idx, len(temps) - 1))

    temp = temps[idx]
    wind = winds[idx]
    wcode = codes[idx]

    return interpret(sentence, temp, wcode, wind)

# ===============================
# 外部调用接口
# ===============================
def query_weather(text: str):
    return chat_weather(text)


