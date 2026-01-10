import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import BytesIO
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

st.set_page_config(layout="wide", page_title="執法/守望地點座標採集工具")

# --- 初始化狀態 ---
if 'data_list' not in st.session_state:
    st.session_state.data_list = [{"序號": i+1, "地點名稱": "", "緯度": None, "經度": None} for i in range(20)]
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = [22.9997, 120.2270] # 預設台南市中心

# 初始化搜尋引擎 (OSM Nominatim)
geolocator = Nominatim(user_agent="police_map_tool")

st.title("🚨 執法/守望地點座標採集工具")
st.markdown("---")

# --- 版面配置 ---
col1, col2 = st.columns([1, 2])

# --- 左側：輸入與列表 ---
with col1:
    st.subheader("📋 座標清單")
    
    current_idx = st.session_state.current_index
    
    # 編輯區
    with st.expander(f"📍 正在編輯第 {current_idx + 1} 筆", expanded=True):
        # 輸入地點名稱
        loc_name = st.text_input("輸入執法位置描述 (例如：中山路中正路口)", 
                                value=st.session_state.data_list[current_idx]["地點名稱"],
                                key=f"input_{current_idx}")
        st.session_state.data_list[current_idx]["地點名稱"] = loc_name
        
        # 搜尋功能
        search_query = st.text_input("🔍 搜尋地圖位置 (輸入後按 Enter 搜尋)", placeholder="台南市中西區中山路")
        if search_query:
            try:
                location = geolocator.geocode(search_query)
                if location:
                    st.session_state.temp_coords = [location.latitude, location.longitude]
                    st.success(f"已搜尋到位置，請在地圖微調點選。")
                else:
                    st.error("找不到該位置，請嘗試更詳細的名稱。")
            except:
                st.warning("搜尋服務繁忙，請稍後再試。")

        # 顯示當前選取的座標
        curr_lat = st.session_state.data_list[current_idx]["緯度"]
        curr_lng = st.session_state.data_list[current_idx]["經度"]
        
        c1, c2 = st.columns(2)
        if c1.button("✅ 確定並存入表格", use_container_width=True):
            if st.session_state.data_list[current_idx]["地點名稱"] == "":
                st.warning("請先輸入地點名稱")
            else:
                # 實際存入座標
                st.session_state.data_list[current_idx]["緯度"] = st.session_state.temp_coords[0]
                st.session_state.data_list[current_idx]["經度"] = st.session_state.temp_coords[1]
                if current_idx < 19:
                    st.session_state.current_index += 1
                st.rerun()
        
        if c2.button("🗑️ 清空本筆資料", use_container_width=True):
            st.session_state.data_list[current_idx] = {"序號": current_idx+1, "地點名稱": "", "緯度": None, "經度": None}
            st.rerun()

    # 列表總覽
    df_display = pd.DataFrame(st.session_state.data_list)
    st.dataframe(df_display, height=400, hide_index=True)

# --- 右側：地圖操作 ---
with col2:
    st.subheader("🗺️ 地圖標註 (台南市區)")
    st.info("💡 步驟：1.搜尋或移動地圖 2.滑鼠點擊路口中心微調 3.按左側「確定」")

    # 地圖中心：如果有 temp_coords 就用 temp_coords，否則預設台南
    m = folium.Map(location=st.session_state.temp_coords, zoom_start=16, control_scale=True)
    
    # 顯示「編輯中」的臨時標籤 (藍色)
    folium.Marker(
        st.session_state.temp_coords,
        popup="當前選取點",
        icon=folium.Icon(color="blue", icon="screenshot", prefix='fa')
    ).add_to(m)

    # 顯示「已儲存」的所有標籤 (紅色)
    for item in st.session_state.data_list:
        if item["緯度"] and item["經度"]:
            folium.Marker(
                [item["緯度"], item["經度"]], 
                popup=item["地點名稱"],
                icon=folium.Icon(color="red")
            ).add_to(m)

    # 顯示地圖並抓取點擊
    map_data = st_folium(m, width="100%", height=600, key="main_map")

    if map_data and map_data.get("last_clicked"):
        new_lat = map_data["last_clicked"]["lat"]
        new_lng = map_data["last_clicked"]["lng"]
        # 更新臨時座標，但不直接寫入 data_list (等待按確定)
        if [new_lat, new_lng] != st.session_state.temp_coords:
            st.session_state.temp_coords = [new_lat, new_lng]
            st.rerun()

# --- 底部：匯出 ---
st.write("---")
df = pd.DataFrame(st.session_state.data_list)
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='座標表')

st.download_button(
    label="📂 匯出一鍵下載 Excel 檔案",
    data=output.getvalue(),
    file_name="執法守望地點座標表.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary"
)

if st.button("🔄 重置整份表單 (清除全部 20 筆)"):
    st.session_state.data_list = [{"序號": i+1, "地點名稱": "", "緯度": None, "經度": None} for i in range(20)]
    st.session_state.current_index = 0
    st.session_state.temp_coords = [22.9997, 120.2270]
    st.rerun()