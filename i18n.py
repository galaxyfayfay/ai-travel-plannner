cat << 'EOF' > i18n.py
import streamlit as st

LANG = {
    "en": {
        "where": "Where are you headed?",
        "build": "🚀 Build my itinerary",
        "retry": "🔄 Try different places",
        "days": "How many days is your trip?",
        "budget": "Daily spending budget (USD)",
        "mustsee": "🔥 Must-see attractions",
        "warning_demo": "Live data unavailable. Showing demo data.",
    },
    "zh": {
        "where": "你要去哪里？",
        "build": "🚀 生成行程",
        "retry": "🔄 换一批推荐",
        "days": "旅行天数",
        "budget": "每日预算（美元）",
        "mustsee": "🔥 当地必去景点",
        "warning_demo": "实时数据获取失败，展示示例数据。",
    },
}

def t(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    return LANG.get(lang, LANG["en"]).get(key, key)
EOF
