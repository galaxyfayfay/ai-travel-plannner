import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from ai_planner import generate_itinerary

st.title("🌏 AI Travel Planner Pro")

# 用户输入
city = st.text_input(
    "Enter city (example: Tokyo, Beijing, Paris)",
    "Tokyo"
)

place_type = st.selectbox(
    "Select place type",
    ["restaurant","cafe","attraction"]
)

days = st.slider("Trip duration (days)",1,5,2)

limit = st.slider("Number of places",5,20,10)

API_KEY = "fd5a842360797574db762b387ec25bbf"

# 城市坐标数据库（避免API解析失败）
city_coordinates = {

"tokyo":(35.6762,139.6503),
"beijing":(39.9042,116.4074),
"shanghai":(31.2304,121.4737),
"paris":(48.8566,2.3522),
"london":(51.5072,-0.1276),
"seoul":(37.5665,126.9780),
"bangkok":(13.7563,100.5018)

}

# 类型转换
type_map = {
"restaurant":"餐厅",
"cafe":"咖啡",
"attraction":"景点"
}


def get_city_location(city):

    city_lower = city.lower()

    if city_lower in city_coordinates:
        return city_coordinates[city_lower]

    return None


def search_places(lat, lon):

    places = []

    # 尝试调用高德 API
    url = "https://restapi.amap.com/v3/place/around"

    params = {
        "key": API_KEY,
        "location": f"{lon},{lat}",
        "radius": 5000,
        "keywords": type_map.get(place_type, place_type),
        "offset": limit
    }

    try:

        r = requests.get(url, params=params, timeout=5).json()

        if r.get("status") == "1":

            for p in r.get("pois", []):

                name = p.get("name", "Unknown")

                location = p.get("location")

                if location:

                    lon_p, lat_p = location.split(",")

                    rating = p.get("biz_ext", {}).get("rating", "0")

                    places.append({
                        "name": name,
                        "lat": float(lat_p),
                        "lon": float(lon_p),
                        "rating": float(rating)
                    })

    except:
        pass


    # 如果 API 没返回数据 → 使用本地示例数据
    if len(places) == 0:

        st.warning("API returned no results. Using demo data instead.")

        places = [
            {"name":"Sample Sushi Bar","lat":lat+0.01,"lon":lon+0.01,"rating":4.7},
            {"name":"City Cafe","lat":lat+0.02,"lon":lon+0.01,"rating":4.5},
            {"name":"Central Restaurant","lat":lat-0.01,"lon":lon-0.01,"rating":4.6},
            {"name":"Local Food Market","lat":lat+0.015,"lon":lon-0.02,"rating":4.4},
            {"name":"Popular Bistro","lat":lat-0.02,"lon":lon+0.01,"rating":4.3}
        ]

    return pd.DataFrame(places)


if st.button("Generate Travel Plan"):

    location=get_city_location(city)

    if location is None:

        st.error(
        "City not supported. Try: Tokyo, Beijing, Shanghai, Paris"
        )

        st.stop()

    lat,lon=location

    df=search_places(lat,lon)

    if df.empty:

        st.warning("No places found from API")

        st.stop()

    df=df.sort_values("rating",ascending=False)

    st.subheader("⭐ Recommended Places")

    st.dataframe(df)

    itinerary=generate_itinerary(df,days)

    st.subheader("🧠 AI Travel Itinerary")

    for day,places in itinerary.items():

        st.write(day)

        for p in places:

            st.write("•",p)

    m=folium.Map(location=[lat,lon],zoom_start=12)

    route=[]

    for _,row in df.iterrows():

        folium.Marker(
            [row["lat"],row["lon"]],
            popup=f"{row['name']} ⭐{row['rating']}"
        ).add_to(m)

        route.append([row["lat"],row["lon"]])

    if len(route)>1:

        folium.PolyLine(route).add_to(m)

    st.subheader("🗺️ Map Route")

    st_folium(m,width=700)