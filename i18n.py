"""i18n.py — Bilingual support (Chinese / English)"""

TRANSLATIONS = {
    "EN": {
        # Hero
        "hero_title": "✈️ Trip Planner",
        "hero_subtitle": "Tell us where you're headed — we'll build your perfect itinerary",
        
        # Sidebar sections
        "where_heading": "🌏 Where are you headed?",
        "pick_country": "🌐 Pick a country or region",
        "pick_city": "🏙️ Which city?",
        "city_override": "✏️ Not in the list? Type any city:",
        "city_placeholder": "e.g. Kyoto, Cusco, Zanzibar, Queenstown…",
        "hotel_label": "🏨 Where are you staying?",
        "hotel_placeholder": "Hotel name or address",
        "depart_label": "🚩 Where do you start on Day 1?",
        "depart_placeholder": "e.g. Tokyo Station, airport arrival point",
        "arrive_label": "🏁 Where do you leave from at the end?",
        "arrive_placeholder": "e.g. Narita Airport, train station",
        
        # Trip planning
        "plan_heading": "🗓️ Plan your days",
        "how_many_days": "How many days is your trip?",
        "what_todo": "What do you want to do?",
        "day_prefs_heading": "Day-by-day preferences",
        "day_prefs_caption": "Customise each day — choose an area, how picky you are about ratings, and how many places to visit.",
        "area_label": "Area",
        "min_rating_label": "Minimum rating (how strict?)",
        "daily_budget_label": "💰 Daily spending budget (USD)",
        "all_area_label": "Which area? (applies to all days)",
        
        # Buttons
        "build_btn": "🚀 Build my itinerary",
        "refresh_btn": "🔄 Try different places",
        
        # Status messages
        "loading_districts": "Loading districts…",
        "loading_neighbourhoods": "Loading neighbourhoods…",
        "finding_dest": "🌐 Finding your destination…",
        "looking_up_locations": "📍 Looking up your saved locations…",
        "finding_places": "🔍 Finding great places in",
        "building_itin": "✨ Putting your itinerary together…",
        
        # Metrics
        "metric_places": "📍 Places",
        "metric_days": "📅 Days",
        "metric_stops": "🗓️ Stops",
        "metric_rating": "⭐ Avg Rating",
        "metric_budget": "💰 Budget",
        
        # Table headers
        "tbl_seq": "#",
        "tbl_day_stop": "Day / Stop",
        "tbl_time": "Time",
        "tbl_place": "Place",
        "tbl_district": "District",
        "tbl_type": "Type",
        "tbl_rating": "Rating",
        "tbl_transport": "Getting There",
        "tbl_contact": "Contact & Address",
        
        # Map section
        "map_heading": "🗺️ Your Route on the Map",
        "map_caption": "Tap a numbered circle to see place details · Tap a route dot for travel info",
        
        # Budget
        "budget_heading": "💰 Cost Estimate (per person, including entry + transport)",
        "budget_over": "🔴 A few days are over your budget. Try reducing the number of stops.",
        "budget_total": "Total Est.",
        "budget_breakdown": "📊 See full cost breakdown",
        
        # Export
        "export_heading": "📤 Save or Share Your Trip",
        "export_download": "📄 Download as a file (open in browser → print to PDF)",
        "export_download_btn": "⬇️ Download itinerary",
        "export_calendar": "📅 Add stops to Google Calendar",
        "export_date": "When does your trip start?",
        "export_caption": "Open the downloaded file in Chrome or Safari, then press Ctrl+P to save as PDF.",
        
        # Recommendations
        "rec_heading": "💡 More Places You Might Like",
        "rec_caption": "These places didn't make it into your itinerary but are worth exploring.",
        "rec_refresh": "🔄",
        
        # Welcome cards
        "welcome_1_icon": "🎯",
        "welcome_1_title": "You decide the mix",
        "welcome_1_desc": "Choose exactly what goes into each day — 2 sights, 1 café, whatever you want",
        "welcome_2_icon": "💰",
        "welcome_2_title": "Stay on budget",
        "welcome_2_desc": "Set a daily budget and see estimated costs in your local currency",
        "welcome_3_icon": "📍",
        "welcome_3_title": "Plan by neighbourhood",
        "welcome_3_desc": "Pick the area you want to explore each day — the app clusters nearby places automatically",
        "welcome_4_icon": "🗺️",
        "welcome_4_title": "No marathon days",
        "welcome_4_desc": "All stops on a given day are kept within 8 km of each other — no exhausting detours",
        
        # Wishlist
        "wishlist_heading": "💫 My Wishlist",
        "wishlist_empty": "Your wishlist is empty. Add places you'd like to visit!",
        "wishlist_add": "❤️ Save to Wishlist",
        "wishlist_remove": "💔 Remove",
        "wishlist_saved": "✅ Saved to wishlist!",
        
        # Points
        "points_heading": "🎫 My Points",
        "points_checkin": "📍 Check In Here",
        "points_checkin_done": "✅ Checked in!",
        "points_redeem": "🎁 Redeem Voucher",
        "points_redeemed": "🎉 Voucher redeemed!",
        "points_balance": "Your points balance",
        "points_history": "Points history",
        
        # Auth
        "auth_login": "🔐 Sign In",
        "auth_register": "📝 Register",
        "auth_logout": "🚪 Sign Out",
        "auth_username": "Username",
        "auth_password": "Password",
        "auth_email": "Email",
        "auth_welcome": "Welcome back",
        "auth_not_logged": "Not signed in",
        "auth_login_required": "Please sign in to use this feature.",
        
        # Collaborate
        "collab_heading": "🤝 Collaborate",
        "collab_invite": "Invite someone to edit",
        "collab_share_link": "📋 Copy share link",
        "collab_email_placeholder": "friend@email.com",
        "collab_send_invite": "Send invite",
        
        # Transport
        "transport_walk": "🚶 Walk",
        "transport_taxi": "🚕 Taxi/Ride-hail",
        "transport_transit": "🚇 Public Transit",
        "transport_drive": "🚗 Self-drive",
        "transport_time": "Travel time",
        "transport_cost": "Est. cost",
        "transport_distance": "Distance",
        
        # Meals
        "meal_breakfast": "🌅 Breakfast",
        "meal_lunch": "☀️ Lunch",
        "meal_dinner": "🌙 Dinner",
        "meal_cafe": "☕ Coffee Break",
        "meal_supper": "🌃 Late Night Snack",
        "meal_recommendation": "Meal Suggestions",
        
        # Must-see
        "mustsee_heading": "⭐ Local Must-See Attractions",
        "mustsee_caption": "Curated highlights for this destination",
        
        # Errors / warnings
        "err_city_not_found": "We couldn't find '{city}' on the map. Try a different spelling or a nearby city.",
        "err_itinerary_failed": "We hit a snag building your itinerary: {err}",
        "err_map_failed": "The map couldn't load: {err}",
        "err_no_places": "No places found. Try a different city, area, or place type.",
        "err_export_failed": "Couldn't generate the download file: {err}",
        "warn_demo_data": "⚠️ Couldn't fetch live data right now — showing sample places so you can try the app.",
        
        # Data source
        "data_source": "📡 Data",
        "data_radius": "Places within 8 km of each other",
        
        # Last stop
        "last_stop": "Last stop of the day",
    },
    
    "ZH": {
        # Hero
        "hero_title": "✈️ 旅行规划助手",
        "hero_subtitle": "告诉我们你要去哪里，我们为你打造完美行程",
        
        # Sidebar sections
        "where_heading": "🌏 你要去哪里？",
        "pick_country": "🌐 选择国家或地区",
        "pick_city": "🏙️ 选择城市",
        "city_override": "✏️ 没找到？直接输入城市名：",
        "city_placeholder": "例如：京都、库斯科、桑给巴尔…",
        "hotel_label": "🏨 你住在哪里？",
        "hotel_placeholder": "酒店名称或地址",
        "depart_label": "🚩 第一天从哪里出发？",
        "depart_placeholder": "例如：东京站、机场",
        "arrive_label": "🏁 最后一天从哪里离开？",
        "arrive_placeholder": "例如：成田机场、火车站",
        
        # Trip planning
        "plan_heading": "🗓️ 规划你的行程",
        "how_many_days": "行程共几天？",
        "what_todo": "你想做什么？",
        "day_prefs_heading": "每日偏好设置",
        "day_prefs_caption": "为每天定制行程——选择区域、评分要求和游览地点数量。",
        "area_label": "区域",
        "min_rating_label": "最低评分（越高越严格）",
        "daily_budget_label": "💰 每日预算（美元）",
        "all_area_label": "选择区域（适用所有天）",
        
        # Buttons
        "build_btn": "🚀 生成我的行程",
        "refresh_btn": "🔄 换一批地点",
        
        # Status messages
        "loading_districts": "正在加载区县信息…",
        "loading_neighbourhoods": "正在加载街区信息…",
        "finding_dest": "🌐 正在定位目的地…",
        "looking_up_locations": "📍 正在查询你的位置…",
        "finding_places": "🔍 正在搜索",
        "building_itin": "✨ 正在规划行程…",
        
        # Metrics
        "metric_places": "📍 地点数",
        "metric_days": "📅 天数",
        "metric_stops": "🗓️ 站点",
        "metric_rating": "⭐ 平均评分",
        "metric_budget": "💰 预算",
        
        # Table headers
        "tbl_seq": "#",
        "tbl_day_stop": "天 / 站",
        "tbl_time": "时间",
        "tbl_place": "地点",
        "tbl_district": "区域",
        "tbl_type": "类型",
        "tbl_rating": "评分",
        "tbl_transport": "交通方式",
        "tbl_contact": "联系与地址",
        
        # Map section
        "map_heading": "🗺️ 路线地图",
        "map_caption": "点击编号圆圈查看详情 · 点击路线点查看交通信息",
        
        # Budget
        "budget_heading": "💰 费用估算（每人，含门票+交通）",
        "budget_over": "🔴 部分天数超出预算，建议减少站点或选择相邻区域以节省交通费用。",
        "budget_total": "总计估算",
        "budget_breakdown": "📊 查看详细费用明细",
        
        # Export
        "export_heading": "📤 保存或分享行程",
        "export_download": "📄 下载文件（在浏览器中打开 → 打印为PDF）",
        "export_download_btn": "⬇️ 下载行程",
        "export_calendar": "📅 添加到谷歌日历",
        "export_date": "行程开始日期？",
        "export_caption": "在Chrome或Safari中打开下载的文件，然后按Ctrl+P（Mac按⌘P）保存为PDF。",
        
        # Recommendations
        "rec_heading": "💡 更多推荐地点",
        "rec_caption": "这些地点未能进入行程，但同样值得一去。",
        "rec_refresh": "🔄",
        
        # Welcome cards
        "welcome_1_icon": "🎯",
        "welcome_1_title": "自由组合",
        "welcome_1_desc": "精确控制每天的行程——2个景点+1家咖啡馆，随你搭配",
        "welcome_2_icon": "💰",
        "welcome_2_title": "轻松控制预算",
        "welcome_2_desc": "设定每日预算，以本地货币显示估算费用",
        "welcome_3_icon": "📍",
        "welcome_3_title": "按街区规划",
        "welcome_3_desc": "选择每天想探索的区域，系统自动聚合附近的地点",
        "welcome_4_icon": "🗺️",
        "welcome_4_title": "告别疲惫打卡",
        "welcome_4_desc": "每天所有站点控制在8公里以内，拒绝长途奔波",
        
        # Wishlist
        "wishlist_heading": "💫 我的心愿单",
        "wishlist_empty": "心愿单是空的，快添加你想去的地方吧！",
        "wishlist_add": "❤️ 加入心愿单",
        "wishlist_remove": "💔 移除",
        "wishlist_saved": "✅ 已加入心愿单！",
        
        # Points
        "points_heading": "🎫 我的积分",
        "points_checkin": "📍 在此签到",
        "points_checkin_done": "✅ 签到成功！",
        "points_redeem": "🎁 兑换优惠券",
        "points_redeemed": "🎉 兑换成功！",
        "points_balance": "当前积分",
        "points_history": "积分记录",
        
        # Auth
        "auth_login": "🔐 登录",
        "auth_register": "📝 注册",
        "auth_logout": "🚪 退出",
        "auth_username": "用户名",
        "auth_password": "密码",
        "auth_email": "邮箱",
        "auth_welcome": "欢迎回来",
        "auth_not_logged": "未登录",
        "auth_login_required": "请先登录以使用此功能。",
        
        # Collaborate
        "collab_heading": "🤝 协作编辑",
        "collab_invite": "邀请他人共同编辑",
        "collab_share_link": "📋 复制分享链接",
        "collab_email_placeholder": "朋友的邮箱",
        "collab_send_invite": "发送邀请",
        
        # Transport
        "transport_walk": "🚶 步行",
        "transport_taxi": "🚕 打车",
        "transport_transit": "🚇 公共交通",
        "transport_drive": "🚗 自驾",
        "transport_time": "行程时间",
        "transport_cost": "估算费用",
        "transport_distance": "距离",
        
        # Meals
        "meal_breakfast": "🌅 早餐",
        "meal_lunch": "☀️ 午餐",
        "meal_dinner": "🌙 晚餐",
        "meal_cafe": "☕ 下午茶",
        "meal_supper": "🌃 宵夜",
        "meal_recommendation": "餐饮推荐",
        
        # Must-see
        "mustsee_heading": "⭐ 当地必游景点",
        "mustsee_caption": "精选当地热门目的地",
        
        # Errors / warnings
        "err_city_not_found": "找不到"{city}"，请尝试其他拼写或邻近城市。",
        "err_itinerary_failed": "行程生成遇到问题：{err}",
        "err_map_failed": "地图加载失败：{err}",
        "err_no_places": "未找到地点，请尝试更换城市、区域或类型。",
        "err_export_failed": "无法生成下载文件：{err}",
        "warn_demo_data": "⚠️ 暂时无法获取实时数据，当前显示示例地点供你体验功能。",
        
        # Data source
        "data_source": "📡 数据来源",
        "data_radius": "站点间距控制在8公里以内",
        
        # Last stop
        "last_stop": "当日最后一站",
    }
}

def t(key: str, lang: str = "EN", **kwargs) -> str:
    """Get translation for key in given language, with optional format args."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["EN"]).get(
        key,
        TRANSLATIONS["EN"].get(key, key)  # fallback to English, then key itself
    )
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
