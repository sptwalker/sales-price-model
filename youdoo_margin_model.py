import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 页面配置
st.set_page_config(page_title="YOUDOO BOX 毛利测算模型 V6.4", layout="wide", page_icon="🎮")
st.title("🎮 YOUDOO BOX 产品毛利测算财务模型 V6.4")
st.caption("✅ 销量-会员收入-毛利强关联修正 | 硬件/续费毛利拆分展示 | 原有布局完全保留")

# -------------------------- 0. Session State 全量初始化 --------------------------
# 渠道占比初始化
if "jd_ratio" not in st.session_state:
    st.session_state.jd_ratio = 15
if "tmall_ratio" not in st.session_state:
    st.session_state.tmall_ratio = 15
if "douyin_ratio" not in st.session_state:
    st.session_state.douyin_ratio = 20
if "offline_ratio" not in st.session_state:
    st.session_state.offline_ratio = 50

# SKU占比初始化
if "online_standard_ratio" not in st.session_state:
    st.session_state.online_standard_ratio = 60
if "online_family_ratio" not in st.session_state:
    st.session_state.online_family_ratio = 40
if "offline_family_ratio" not in st.session_state:
    st.session_state.offline_family_ratio = 80
if "offline_luxury_ratio" not in st.session_state:
    st.session_state.offline_luxury_ratio = 20

# 套装价格初始化
if "std_guide" not in st.session_state:
    st.session_state.std_guide = 1899
if "std_promo" not in st.session_state:
    st.session_state.std_promo = 1799
if "fam_guide" not in st.session_state:
    st.session_state.fam_guide = 2199
if "fam_promo" not in st.session_state:
    st.session_state.fam_promo = 1999
if "lux_guide" not in st.session_state:
    st.session_state.lux_guide = 2899
if "lux_promo" not in st.session_state:
    st.session_state.lux_promo = 2699

# 渠道成本费率初始化
if "jd_rate_early" not in st.session_state:
    st.session_state.jd_rate_early = 40
if "jd_rate_late" not in st.session_state:
    st.session_state.jd_rate_late = 15
if "tmall_rate_early" not in st.session_state:
    st.session_state.tmall_rate_early = 40
if "tmall_rate_late" not in st.session_state:
    st.session_state.tmall_rate_late = 15
if "douyin_rate_early" not in st.session_state:
    st.session_state.douyin_rate_early = 60
if "douyin_rate_late" not in st.session_state:
    st.session_state.douyin_rate_late = 20
if "offline_rate_early" not in st.session_state:
    st.session_state.offline_rate_early = 40
if "offline_rate_late" not in st.session_state:
    st.session_state.offline_rate_late = 30

# -------------------------- 回调函数 --------------------------
# 渠道占比联动回调
def on_channel_change(changed_key):
    jd = st.session_state.jd_ratio
    tmall = st.session_state.tmall_ratio
    douyin = st.session_state.douyin_ratio
    offline = st.session_state.offline_ratio
    
    total = jd + tmall + douyin + offline
    if total == 0:
        return
    
    delta = total - 100
    other_keys = [k for k in ["jd_ratio", "tmall_ratio", "douyin_ratio", "offline_ratio"] if k != changed_key]
    other_total = sum([st.session_state[k] for k in other_keys])
    
    if other_total == 0:
        per_delta = delta / len(other_keys)
        for k in other_keys:
            st.session_state[k] = max(0, min(100, st.session_state[k] - per_delta))
    else:
        for k in other_keys:
            ratio = st.session_state[k] / other_total
            st.session_state[k] = max(0, min(100, st.session_state[k] - delta * ratio))

# 线上SKU占比联动回调
def on_online_sku_change(changed_key):
    if changed_key == "online_standard_ratio":
        st.session_state.online_family_ratio = 100 - st.session_state.online_standard_ratio
    else:
        st.session_state.online_standard_ratio = 100 - st.session_state.online_family_ratio
    st.session_state.online_standard_ratio = max(0, min(100, st.session_state.online_standard_ratio))
    st.session_state.online_family_ratio = max(0, min(100, st.session_state.online_family_ratio))

# 线下SKU占比联动回调
def on_offline_sku_change(changed_key):
    if changed_key == "offline_family_ratio":
        st.session_state.offline_luxury_ratio = 100 - st.session_state.offline_family_ratio
    else:
        st.session_state.offline_family_ratio = 100 - st.session_state.offline_luxury_ratio
    st.session_state.offline_family_ratio = max(0, min(100, st.session_state.offline_family_ratio))
    st.session_state.offline_luxury_ratio = max(0, min(100, st.session_state.offline_luxury_ratio))

# 价格微调回调函数
def adjust_price(key, delta):
    st.session_state[key] += delta
    st.session_state[key] = max(1000, min(5000, st.session_state[key]))

# -------------------------- 1. 预设基础数据 --------------------------
sku_base_config = {
    "标准版": {
        "offline_available": False,
        "default_extra_remote": 0,
        "default_light_gun": 0,
        "default_vip_month": 1,
        "default_vip_year": 0,
        "default_parent_card": 0,
        "default_nfc_full": 0,
        "default_nfc_ssr": 0
    },
    "家庭版": {
        "offline_available": True,
        "default_extra_remote": 0,
        "default_light_gun": 0,
        "default_vip_month": 0,
        "default_vip_year": 1,
        "default_parent_card": 1,
        "default_nfc_full": 1,
        "default_nfc_ssr": 0
    },
    "豪华版": {
        "offline_available": True,
        "default_extra_remote": 1,
        "default_light_gun": 2,
        "default_vip_month": 0,
        "default_vip_year": 2,
        "default_parent_card": 1,
        "default_nfc_full": 0,
        "default_nfc_ssr": 1
    }
}
sku_list = list(sku_base_config.keys())
online_channel = ["京东", "天猫", "抖音"]
offline_channel = ["线下"]
all_channel = online_channel + offline_channel

# 单品成本预设
item_cost = {
    "remote": 120,
    "light_gun": 89,
    "vip_month": 49,
    "vip_year": 358,
    "parent_card": 49,
    "nfc_full": 49,
    "nfc_ssr": 99,
    "card_cost_rate": 0.2
}

# -------------------------- 2. 侧边栏参数面板 --------------------------
# 第一区：全渠道销量与分配
st.sidebar.header("📊 全渠道销量与分配")
total_sales_volume = st.sidebar.slider("全渠道总销售总量（台）", 20000, 500000, 100000, step=10000)

st.sidebar.caption("✅ 渠道占比自动联动，总和永远100%")
jd_ratio = st.sidebar.slider("京东销量占比（%）", 0, 100, key="jd_ratio", on_change=on_channel_change, args=("jd_ratio",))
tmall_ratio = st.sidebar.slider("天猫销量占比（%）", 0, 100, key="tmall_ratio", on_change=on_channel_change, args=("tmall_ratio",))
douyin_ratio = st.sidebar.slider("抖音销量占比（%）", 0, 100, key="douyin_ratio", on_change=on_channel_change, args=("douyin_ratio",))
offline_ratio = st.sidebar.slider("线下销量占比（%）", 0, 100, key="offline_ratio", on_change=on_channel_change, args=("offline_ratio",))

# 计算各渠道最终销量
channel_volume_dict = {
    "京东": int(total_sales_volume * jd_ratio / 100),
    "天猫": int(total_sales_volume * tmall_ratio / 100),
    "抖音": int(total_sales_volume * douyin_ratio / 100),
    "线下": total_sales_volume - int(total_sales_volume * jd_ratio / 100) - int(total_sales_volume * tmall_ratio / 100) - int(total_sales_volume * douyin_ratio / 100)
}
online_total_volume = sum([channel_volume_dict[ch] for ch in online_channel])
offline_total_volume = channel_volume_dict["线下"]

# 第二区：独立渠道成本设置区
st.sidebar.divider()
st.sidebar.header("💰 渠道成本费率设置（%）")
st.sidebar.caption("独立设置各渠道前期/后期成本占比")
col_ch_rate1, col_ch_rate2 = st.sidebar.columns(2)
with col_ch_rate1:
    st.markdown("**京东**")
    jd_rate_early = st.slider("前期", 0, 80, key="jd_rate_early")
    jd_rate_late = st.slider("后期", 0, 80, key="jd_rate_late")
    
    st.markdown("**抖音**")
    douyin_rate_early = st.slider("前期", 0, 80, key="douyin_rate_early")
    douyin_rate_late = st.slider("后期", 0, 80, key="douyin_rate_late")
with col_ch_rate2:
    st.markdown("**天猫**")
    tmall_rate_early = st.slider("前期", 0, 80, key="tmall_rate_early")
    tmall_rate_late = st.slider("后期", 0, 80, key="tmall_rate_late")
    
    st.markdown("**线下**")
    offline_rate_early = st.slider("前期", 0, 80, key="offline_rate_early")
    offline_rate_late = st.slider("后期", 0, 80, key="offline_rate_late")

# 选择当前使用的渠道成本阶段
use_channel_stage = st.sidebar.radio("当前渠道成本阶段", ["前期", "后期"], index=0)

# 汇总当前渠道成本费率
channel_rate_config = {
    "京东": jd_rate_early if use_channel_stage == "前期" else jd_rate_late,
    "天猫": tmall_rate_early if use_channel_stage == "前期" else tmall_rate_late,
    "抖音": douyin_rate_early if use_channel_stage == "前期" else douyin_rate_late,
    "线下": offline_rate_early if use_channel_stage == "前期" else offline_rate_late
}

# 第三区：多SKU销量占比分配
st.sidebar.divider()
st.sidebar.subheader("🎮 多SKU销量占比分配")
st.sidebar.caption("规则：线上仅售标准版/家庭版，线下仅售家庭版/豪华版 | 自动联动归一化")

# 线上SKU占比
st.sidebar.markdown("**线上渠道SKU占比**")
online_standard_ratio = st.sidebar.slider("标准版线上占比（%）", 0, 100, key="online_standard_ratio", on_change=on_online_sku_change, args=("online_standard_ratio",))
online_family_ratio = st.sidebar.slider("家庭版线上占比（%）", 0, 100, key="online_family_ratio", on_change=on_online_sku_change, args=("online_family_ratio",))

# 线下SKU占比
st.sidebar.markdown("**线下渠道SKU占比**")
offline_family_ratio = st.sidebar.slider("家庭版线下占比（%）", 0, 100, key="offline_family_ratio", on_change=on_offline_sku_change, args=("offline_family_ratio",))
offline_luxury_ratio = st.sidebar.slider("豪华版线下占比（%）", 0, 100, key="offline_luxury_ratio", on_change=on_offline_sku_change, args=("offline_luxury_ratio",))

# 计算各SKU最终销量
online_standard_volume = int(online_total_volume * online_standard_ratio / 100)
online_family_volume = online_total_volume - online_standard_volume
online_luxury_volume = 0
offline_family_volume = int(offline_total_volume * offline_family_ratio / 100)
offline_luxury_volume = offline_total_volume - offline_family_volume
sku_total_volume = {
    "标准版": online_standard_volume,
    "家庭版": online_family_volume + offline_family_volume,
    "豪华版": offline_luxury_volume
}

# 第四区：产品套装价格设定
st.sidebar.divider()
st.sidebar.header("📦 产品套装价格设定")
price_mode = st.sidebar.radio("售价模式", ["官方指导价", "大促价"], index=1)

# 侧边栏专用价格控制组件
def sidebar_price_control(key, label, min_val, max_val):
    st.sidebar.markdown(f"**▸ {label}**")
    price_val = st.sidebar.slider("", min_val, max_val, key=key)
    col_btn1, col_btn2, col_btn3, col_btn4 = st.sidebar.columns(4)
    with col_btn1:
        st.button("➖10", key=f"{key}_minus10", on_click=adjust_price, args=(key, -10))
    with col_btn2:
        st.button("➖1", key=f"{key}_minus1", on_click=adjust_price, args=(key, -1))
    with col_btn3:
        st.button("➕1", key=f"{key}_plus1", on_click=adjust_price, args=(key, 1))
    with col_btn4:
        st.button("➕10", key=f"{key}_plus10", on_click=adjust_price, args=(key, 10))
    return price_val

std_guide_price = sidebar_price_control("std_guide", "标准版官方指导价", 1500, 2500)
std_promo_price = sidebar_price_control("std_promo", "标准版大促价", 1400, 2400)
st.sidebar.markdown("---")
fam_guide_price = sidebar_price_control("fam_guide", "家庭版官方指导价", 1800, 2800)
fam_promo_price = sidebar_price_control("fam_promo", "家庭版大促价", 1700, 2700)
st.sidebar.markdown("---")
lux_guide_price = sidebar_price_control("lux_guide", "豪华版官方指导价", 2200, 3500)
lux_promo_price = sidebar_price_control("lux_promo", "豪华版大促价", 2100, 3400)

# 汇总SKU价格配置
sku_price_config = {
    "标准版": {"guide_price": std_guide_price, "promo_price": std_promo_price},
    "家庭版": {"guide_price": fam_guide_price, "promo_price": fam_promo_price},
    "豪华版": {"guide_price": lux_guide_price, "promo_price": lux_promo_price}
}

# 第五区：套装赠品/附件配置区
st.sidebar.divider()
st.sidebar.header("🎁 套装赠品/附件配置")
selected_sku_for_config = st.sidebar.selectbox("选择要配置的套装", sku_list)
st.sidebar.markdown(f"**▸ {selected_sku_for_config} 赠品数量配置**")
sku_default_config = sku_base_config[selected_sku_for_config]
col_gift1, col_gift2 = st.sidebar.columns(2)
with col_gift1:
    extra_remote = st.number_input("额外遥控器数量", 0, 10, sku_default_config["default_extra_remote"])
    light_gun = st.number_input("光枪数量", 0, 10, sku_default_config["default_light_gun"])
    vip_month = st.number_input("VIP月卡数量", 0, 24, sku_default_config["default_vip_month"])
    vip_year = st.number_input("VIP年卡数量", 0, 10, sku_default_config["default_vip_year"])
with col_gift2:
    parent_card = st.number_input("家长钥匙卡数量", 0, 5, sku_default_config["default_parent_card"])
    nfc_full = st.number_input("NFC全套卡数量", 0, 5, sku_default_config["default_nfc_full"])
    nfc_ssr = st.number_input("NFC SSR卡数量", 0, 5, sku_default_config["default_nfc_ssr"])
# 更新当前配置的SKU赠品参数
sku_base_config[selected_sku_for_config].update({
    "default_extra_remote": extra_remote,
    "default_light_gun": light_gun,
    "default_vip_month": vip_month,
    "default_vip_year": vip_year,
    "default_parent_card": parent_card,
    "default_nfc_full": nfc_full,
    "default_nfc_ssr": nfc_ssr
})

# 第六区：会员续费收入设置区
st.sidebar.divider()
st.sidebar.header("📅 会员续费收入设置")
st.sidebar.caption("赠送会员到期后，用户主动续费的收入计算")
col_vip1, col_vip2 = st.sidebar.columns(2)
with col_vip1:
    renew_vip_year_price = st.slider("续费年卡价格（元）", 200, 500, 358)
    renew_rate = st.slider("会员续费率（%）", 10, 90, 60, format="%d%%")
    renew_years = 1
with col_vip2:
    renew_vip_month_price = st.slider("续费月卡价格（元）", 20, 80, 49)
    year_card_renew_ratio = st.slider("年卡续费占比（%）", 0, 100, 80, format="%d%%")
st.sidebar.caption("年卡续费占比：续费用户中选择年卡的比例，剩余用户选择月卡")

# 第七区：其他分账与成本参数
st.sidebar.divider()
st.sidebar.subheader("💰 其他分账与成本参数")
royalty_fee = st.sidebar.slider("单台版权费（创维→创想，元）", 100, 300, 200)
vip_split_rate_pct = st.sidebar.slider("会员收入创维分成比例", 0, 50, 20, format="%d%%")
vip_split_rate = vip_split_rate_pct / 100
vip_discount_rate_pct = st.sidebar.slider("赠送会员折价计提比例", 0, 100, 50, format="%d%%")
vip_discount_rate = vip_discount_rate_pct / 100
base_hardware_cost = st.sidebar.number_input("基础硬件成本（含标配/运输/售后，元）", value=984)

# -------------------------- 3. 核心财务计算（强关联修正版） --------------------------
sku_calc_detail = {}
# 硬件销售基础数据
total_skyworth_hardware_profit = 0
total_youduo_hardware_profit = 0
total_revenue = 0
total_channel_cost = 0
total_p_hw = 0
total_p_sw = 0
total_c_hw_base = 0
total_c_hw_extra = 0
total_r_royalty = 0
total_s_split = 0
total_c_card = 0
total_c_vip_discount = 0
channel_cost_detail = []

# 双数据饼图数据准备
sku_sales_amount = {}
sku_sales_cost = {}

# 【修正1】SKU维度硬件毛利计算，为续费基数做准备
for sku in sku_list:
    sku_config = sku_base_config[sku]
    sku_vol = sku_total_volume[sku]
    if sku_vol == 0:
        continue
    
    # 计算售价
    sku_price = sku_price_config[sku]["guide_price"] if price_mode == "官方指导价" else sku_price_config[sku]["promo_price"]
    
    # 渠道成本按百分比计算
    sku_online_vol = online_standard_volume if sku == "标准版" else (online_family_volume if sku == "家庭版" else 0)
    sku_offline_vol = 0 if sku == "标准版" else (offline_family_volume if sku == "家庭版" else offline_luxury_volume)
    sku_total_vol = sku_online_vol + sku_offline_vol
    
    # 加权平均单台渠道费率&成本
    if sku_total_vol > 0:
        online_rate_total = 0
        for ch in online_channel:
            online_rate_total += channel_rate_config[ch] * (channel_volume_dict[ch] / online_total_volume) if online_total_volume > 0 else 0
        offline_rate = channel_rate_config["线下"]
        avg_channel_rate = (online_rate_total * sku_online_vol + offline_rate * sku_offline_vol) / sku_total_vol
        avg_channel_cost_per = sku_price * avg_channel_rate / 100
    else:
        avg_channel_rate = 0
        avg_channel_cost_per = 0
    
    # 赠品&会员成本计算
    extra_hardware_cost = (
        sku_config["default_extra_remote"] * item_cost["remote"]
        + sku_config["default_light_gun"] * item_cost["light_gun"]
    )
    vip_total_price = (
        sku_config["default_vip_month"] * item_cost["vip_month"]
        + sku_config["default_vip_year"] * item_cost["vip_year"]
    )
    card_total_price = (
        sku_config["default_parent_card"] * item_cost["parent_card"]
        + sku_config["default_nfc_full"] * item_cost["nfc_full"]
        + sku_config["default_nfc_ssr"] * item_cost["nfc_ssr"]
    )
    p_hw_per = sku_price - vip_total_price - card_total_price
    p_sw_per = vip_total_price + card_total_price
    card_cost_per = card_total_price * item_cost["card_cost_rate"]
    vip_discount_cost_per = vip_total_price * vip_discount_rate
    s_split_per = vip_total_price * vip_split_rate
    
    # 双主体单台硬件毛利计算
    skyworth_profit_per = p_hw_per + s_split_per - base_hardware_cost - extra_hardware_cost - avg_channel_cost_per - royalty_fee
    youduo_profit_per = p_sw_per + royalty_fee - s_split_per - card_cost_per - vip_discount_cost_per
    
    # 双数据饼图数据
    sku_total_revenue = sku_price * sku_vol
    sku_total_cost = (base_hardware_cost + extra_hardware_cost + avg_channel_cost_per + card_cost_per) * sku_vol
    sku_sales_amount[sku] = sku_total_revenue
    sku_sales_cost[sku] = sku_total_cost
    
    # 保存明细
    sku_calc_detail[sku] = {
        "销量": sku_vol,
        "单台售价": sku_price,
        "单台渠道费率": f"{round(avg_channel_rate,2)}%",
        "单台渠道成本": round(avg_channel_cost_per,2),
        "单台创维硬件毛利": round(skyworth_profit_per,2),
        "单台创想硬件毛利": round(youduo_profit_per,2),
        "创维硬件总毛利": round(skyworth_profit_per * sku_vol,2),
        "创想硬件总毛利": round(youduo_profit_per * sku_vol,2),
        "综合硬件毛利率": round((skyworth_profit_per + youduo_profit_per) / sku_price * 100, 2)
    }
    
    # 全量数据汇总
    total_skyworth_hardware_profit += skyworth_profit_per * sku_vol
    total_youduo_hardware_profit += youduo_profit_per * sku_vol
    total_revenue += sku_price * sku_vol
    total_channel_cost += avg_channel_cost_per * sku_vol
    total_p_hw += p_hw_per * sku_vol
    total_p_sw += p_sw_per * sku_vol
    total_c_hw_base += base_hardware_cost * sku_vol
    total_c_hw_extra += extra_hardware_cost * sku_vol
    total_r_royalty += royalty_fee * sku_vol
    total_s_split += s_split_per * sku_vol
    total_c_card += card_cost_per * sku_vol
    total_c_vip_discount += vip_discount_cost_per * sku_vol

# 【修正2】会员续费收入强关联计算（和总销量100%线性绑定）
# 单用户年均续费收入（固定值，由会员参数决定）
month_card_renew_ratio = 1 - year_card_renew_ratio / 100
single_user_year_renew_revenue = (renew_rate / 100) * (
    (year_card_renew_ratio / 100) * renew_vip_year_price
    + month_card_renew_ratio * renew_vip_month_price * 12
)
# 累计总续费收入（和总销量完全线性相关）
total_renew_revenue = total_sales_volume * single_user_year_renew_revenue * renew_years
# 双主体分账（严格按规则）
total_skyworth_renew_profit = total_renew_revenue * vip_split_rate
total_youduo_renew_profit = total_renew_revenue * (1 - vip_split_rate)
# 最终总毛利（硬件+续费）
total_skyworth_profit = total_skyworth_hardware_profit + total_skyworth_renew_profit
total_youduo_profit = total_youduo_hardware_profit + total_youduo_renew_profit
total_profit = total_skyworth_profit + total_youduo_profit

# 计算加权平均单台数据
if total_sales_volume > 0:
    avg_price_per = total_revenue / total_sales_volume
    avg_channel_cost_per = total_channel_cost / total_sales_volume
    avg_channel_rate = avg_channel_cost_per / avg_price_per * 100
    avg_p_hw_per = total_p_hw / total_sales_volume
    avg_p_sw_per = total_p_sw / total_sales_volume
    avg_c_hw_base_per = total_c_hw_base / total_sales_volume
    avg_c_hw_extra_per = total_c_hw_extra / total_sales_volume
    avg_r_royalty_per = total_r_royalty / total_sales_volume
    avg_s_split_per = total_s_split / total_sales_volume
    avg_c_card_per = total_c_card / total_sales_volume
    avg_c_vip_discount_per = total_c_vip_discount / total_sales_volume
    avg_skyworth_profit_per = total_skyworth_profit / total_sales_volume
    avg_youduo_profit_per = total_youduo_profit / total_sales_volume
    # 单台对应续费收入
    avg_renew_revenue_per = total_renew_revenue / total_sales_volume
else:
    avg_price_per = 0
    avg_channel_cost_per = 0
    avg_channel_rate = 0
    avg_skyworth_profit_per = 0
    avg_youduo_profit_per = 0
    avg_renew_revenue_per = 0

# 渠道成本明细汇总
for ch in all_channel:
    ch_vol = channel_volume_dict[ch]
    ch_rate = channel_rate_config[ch]
    # 该渠道加权平均售价
    ch_sku_price_total = 0
    ch_sku_vol_total = 0
    if ch in online_channel:
        ch_sku_price_total += std_promo_price * online_standard_volume if price_mode == "大促价" else std_guide_price * online_standard_volume
        ch_sku_price_total += fam_promo_price * online_family_volume if price_mode == "大促价" else fam_guide_price * online_family_volume
        ch_sku_vol_total = online_total_volume
    else:
        ch_sku_price_total += fam_promo_price * offline_family_volume if price_mode == "大促价" else fam_guide_price * offline_family_volume
        ch_sku_price_total += lux_promo_price * offline_luxury_volume if price_mode == "大促价" else lux_guide_price * offline_luxury_volume
        ch_sku_vol_total = offline_total_volume
    ch_avg_price = ch_sku_price_total / ch_sku_vol_total if ch_sku_vol_total > 0 else 0
    ch_cost_per = ch_avg_price * ch_rate / 100
    ch_total_cost = ch_vol * ch_cost_per
    channel_cost_detail.append({
        "渠道": ch,
        "销量（台）": ch_vol,
        "销量占比（%）": jd_ratio if ch == "京东" else (tmall_ratio if ch == "天猫" else (douyin_ratio if ch == "抖音" else offline_ratio)),
        "当前渠道费率": f"{ch_rate}%",
        "单台成本（元）": round(ch_cost_per,2),
        "总成本（万元）": round(ch_total_cost / 10000, 2)
    })
channel_cost_df = pd.DataFrame(channel_cost_detail)
sku_summary_df = pd.DataFrame.from_dict(sku_calc_detail, orient="index").reset_index().rename(columns={"index": "SKU版本"})

# -------------------------- 4. 主界面展示（关联显性化） --------------------------
# 核心指标卡片（拆分硬件/续费毛利，关联显性化）
st.divider()
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("全渠道总销量", f"{total_sales_volume:,} 台", f"单台平均售价 {round(avg_price_per,2)} 元")
with col2:
    st.metric("渠道综合成本", f"{round(total_channel_cost/10000,2)} 万元", f"单台平均 {round(avg_channel_cost_per,2)} 元")
with col3:
    skyworth_color = "green" if total_skyworth_profit >= 0 else "red"
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; border: 1px solid #e6e6e6;">
        <p style="margin:0; font-size:14px; color:#555;">创维数字总毛利</p>
        <h3 style="margin:5px 0; color:{skyworth_color};">{round(total_skyworth_profit/10000,2)} 万元</h3>
        <p style="margin:0; font-size:12px;">硬件：{round(total_skyworth_hardware_profit/10000,2)}万 | 续费：{round(total_skyworth_renew_profit/10000,2)}万</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    youduo_color = "green" if total_youduo_profit >= 0 else "red"
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; border: 1px solid #e6e6e6;">
        <p style="margin:0; font-size:14px; color:#555;">创想悦动总毛利</p>
        <h3 style="margin:5px 0; color:{youduo_color};">{round(total_youduo_profit/10000,2)} 万元</h3>
        <p style="margin:0; font-size:12px;">硬件：{round(total_youduo_hardware_profit/10000,2)}万 | 续费：{round(total_youduo_renew_profit/10000,2)}万</p>
    </div>
    """, unsafe_allow_html=True)
with col5:
    total_color = "green" if total_profit >= 0 else "red"
    total_margin_rate = round(total_profit / (total_revenue + total_renew_revenue) * 100, 2) if (total_revenue + total_renew_revenue) >0 else 0
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; border: 1px solid #e6e6e6;">
        <p style="margin:0; font-size:14px; color:#555;">产品总毛利</p>
        <h3 style="margin:5px 0; color:{total_color};">{round(total_profit/10000,2)} 万元</h3>
        <p style="margin:0; font-size:12px;">综合毛利率 {total_margin_rate}%</p>
    </div>
    """, unsafe_allow_html=True)

# 【显性化展示】会员续费收入和销量的强关联
st.markdown(f"""
<div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
    <h4 style="margin:0 0 10px 0;">📈 销量-会员收入-毛利联动校验</h4>
    <p style="margin:5px 0;">• 总续费用户基数：<b>{total_sales_volume:,} 台</b>（和总销量完全绑定）</p>
    <p style="margin:5px 0;">• 单用户年均续费收入：<b>{round(single_user_year_renew_revenue,2)} 元</b>（由会员价格、续费率决定）</p>
    <p style="margin:5px 0;">• {renew_years}年累计续费总收入：<b>{round(total_renew_revenue/10000,2)} 万元</b>（销量涨10倍，续费收入同步涨10倍）</p>
</div>
""", unsafe_allow_html=True)

# 资金流向桑基图
st.divider()
st.subheader("💸 加权平均单台资金流向图（硬件销售部分）")
sankey_labels = [
    "消费者支付", "渠道成本", "创维数字总收入", "创想悦动总收入",
    "基础硬件成本", "额外配件成本", "支付创想版权费", "创维数字毛利",
    "支付创维会员分成", "卡件成本", "赠送会员折价成本", "创想悦动毛利"
]
sankey_source = [0, 0, 0, 2, 2, 2, 2, 8, 6, 3, 3, 3, 3]
sankey_target = [1, 2, 3, 4, 5, 6, 7, 2, 3, 8, 9, 10, 11]
sankey_values = [
    avg_channel_cost_per, avg_p_hw_per, avg_p_sw_per,
    avg_c_hw_base_per, avg_c_hw_extra_per, avg_r_royalty_per, max(total_skyworth_hardware_profit/total_sales_volume, 0) if total_sales_volume>0 else 0,
    avg_s_split_per, avg_r_royalty_per, avg_s_split_per, avg_c_card_per, avg_c_vip_discount_per, max(total_youduo_hardware_profit/total_sales_volume, 0) if total_sales_volume>0 else 0
]
sankey_colors = [
    "#1f77b4", "#d62728", "#ff7f0e", "#2ca02c",
    "#d62728", "#d62728", "#9467bd", "#2ecc71",
    "#9467bd", "#d62728", "#d62728", "#2ecc71"
]
fig_sankey = go.Figure(go.Sankey(
    node=dict(
        pad=20, 
        thickness=25, 
        line=dict(color="#333", width=0.8), 
        label=sankey_labels, 
        color=sankey_colors
    ),
    link=dict(
        source=sankey_source, 
        target=sankey_target, 
        value=sankey_values, 
        color=["rgba(214, 39, 40, 0.3)"]*13
    )
))
fig_sankey.update_layout(
    title_text="加权平均单台产品资金流向拆解（单位：元）", 
    font_size=13, 
    height=600,
    font=dict(color="black")
)
st.plotly_chart(fig_sankey, use_container_width=True)

# 各SKU销量与毛利明细
st.divider()
st.subheader("🎮 各SKU销量与硬件毛利明细")
col_sku1, col_sku2 = st.columns([1.2, 1])
with col_sku1:
    st.dataframe(sku_summary_df, use_container_width=True, hide_index=True)
with col_sku2:
    # 双数据饼图：销售金额+销售成本
    if sku_sales_amount and sku_sales_cost:
        from plotly.subplots import make_subplots
        pie_df_amount = pd.DataFrame({
            "SKU": list(sku_sales_amount.keys()),
            "金额（万元）": [v/10000 for v in sku_sales_amount.values()],
            "类型": "销售金额"
        })
        pie_df_cost = pd.DataFrame({
            "SKU": list(sku_sales_cost.keys()),
            "金额（万元）": [v/10000 for v in sku_sales_cost.values()],
            "类型": "销售成本"
        })
        fig_pie_dual = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]],
                                     subplot_titles=("各SKU销售金额占比", "各SKU销售成本占比"))
        fig_pie_dual.add_trace(
            go.Pie(labels=pie_df_amount["SKU"], values=pie_df_amount["金额（万元）"], 
                   name="销售金额", hole=0.4, domain=dict(x=[0, 0.45])),
            row=1, col=1
        )
        fig_pie_dual.add_trace(
            go.Pie(labels=pie_df_cost["SKU"], values=pie_df_cost["金额（万元）"], 
                   name="销售成本", hole=0.4, domain=dict(x=[0.55, 1])),
            row=1, col=2
        )
        fig_pie_dual.update_layout(height=400)
        st.plotly_chart(fig_pie_dual, use_container_width=True)

# 全渠道成本明细
st.divider()
st.subheader("📊 全渠道成本明细")
col_channel1, col_channel2 = st.columns([1.2, 1])
with col_channel1:
    st.dataframe(channel_cost_df, use_container_width=True, hide_index=True)
    st.metric("渠道总成本合计", f"{round(total_channel_cost/10000,2)} 万元", f"综合费率 {round(avg_channel_rate,2)}%")
with col_channel2:
    fig_channel_pie = px.pie(channel_cost_df, values="总成本（万元）", names="渠道", title="各渠道成本占比", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig_channel_pie, use_container_width=True)

# 双主体明细拆解
st.divider()
st.subheader("📋 双主体收入成本明细（万元）")
col_detail1, col_detail2 = st.columns(2)
with col_detail1:
    st.subheader("创维数字（销售主体）")
    skyworth_detail_df = pd.DataFrame({
        "项目": ["硬件销售收入", "加：捆绑会员分成收入", "加：续费会员分成收入", "减：基础硬件总成本", "减：额外配件总成本", "减：渠道总成本", "减：支付创想版权费", "总毛利"],
        "金额（万元）": [
            round(total_p_hw/10000,2),
            round(total_s_split/10000,2),
            round(total_skyworth_renew_profit/10000,2),
            round(-total_c_hw_base/10000,2),
            round(-total_c_hw_extra/10000,2),
            round(-total_channel_cost/10000,2),
            round(-total_r_royalty/10000,2),
            round(total_skyworth_profit/10000,2)
        ]
    })
    st.dataframe(skyworth_detail_df, use_container_width=True, hide_index=True)
with col_detail2:
    st.subheader("创想悦动（运营主体）")
    youduo_detail_df = pd.DataFrame({
        "项目": ["捆绑软件服务总收入（会员+卡件）", "加：硬件版权费收入", "加：续费会员服务收入", "减：支付创维会员分成", "减：卡件总成本", "减：赠送会员折价总成本", "总毛利"],
        "金额（万元）": [
            round(total_p_sw/10000,2),
            round(total_r_royalty/10000,2),
            round(total_youduo_renew_profit/10000,2),
            round(-(total_s_split + total_skyworth_renew_profit)/10000,2),
            round(-total_c_card/10000,2),
            round(-total_c_vip_discount/10000,2),
            round(total_youduo_profit/10000,2)
        ]
    })
    st.dataframe(youduo_detail_df, use_container_width=True, hide_index=True)

# 【修正3】敏感性分析（强化销量-毛利的关联展示）
st.divider()
st.subheader("📈 销量与硬件成本对毛利影响的敏感性分析（含续费收入）")
st.caption("清晰展示销量变化对硬件毛利、续费毛利、总毛利的线性影响")

# 准备敏感性分析数据（强化销量维度）
hw_cost_range = np.linspace(base_hardware_cost - 100, base_hardware_cost + 100, 8)
volume_levels = [50000, 100000, 200000, 300000, 500000]  # 销量梯度

sensitivity_data = []
for vol in volume_levels:
    for hw_cost in hw_cost_range:
        # 硬件毛利计算
        skyworth_hw_profit_per = avg_p_hw_per + avg_s_split_per - hw_cost - avg_c_hw_extra_per - avg_channel_cost_per - royalty_fee
        youduo_hw_profit_per = avg_p_sw_per + royalty_fee - avg_s_split_per - avg_c_card_per - avg_c_vip_discount_per
        # 续费毛利计算（和销量强线性绑定）
        single_user_renew = (renew_rate / 100) * (
            (year_card_renew_ratio / 100) * renew_vip_year_price
            + (1 - year_card_renew_ratio/100) * renew_vip_month_price * 12
        )
        total_renew = vol * single_user_renew * renew_years
        skyworth_renew = total_renew * vip_split_rate
        youduo_renew = total_renew * (1 - vip_split_rate)
        # 总毛利
        skyworth_total = (skyworth_hw_profit_per * vol + skyworth_renew) / 10000
        youduo_total = (youduo_hw_profit_per * vol + youduo_renew) / 10000
        
        sensitivity_data.append({
            "硬件成本（元）": hw_cost,
            "销量（台）": vol,
            "创维总毛利（万元）": skyworth_total,
            "创想总毛利（万元）": youduo_total,
            "续费毛利合计（万元）": (skyworth_renew + youduo_renew)/10000
        })
sensitivity_df = pd.DataFrame(sensitivity_data)

# 双变量敏感性折线图（强化销量关联）
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.subheader("1. 硬件成本-毛利线性关联图")
    st.caption("X轴：硬件成本 | 不同颜色：不同销量 | 左Y轴：创维总毛利 | 右Y轴：创想总毛利")
    fig_line = go.Figure()
    colors = px.colors.qualitative.D3
    for i, vol in enumerate(volume_levels):
        df_sub = sensitivity_df[sensitivity_df["销量（台）"] == vol]
        fig_line.add_trace(go.Scatter(
            x=df_sub["硬件成本（元）"], y=df_sub["创维总毛利（万元）"],
            name=f"创维-销量{vol}台",
            line=dict(color=colors[i % len(colors)], dash="solid"),
            yaxis="y"
        ))
        fig_line.add_trace(go.Scatter(
            x=df_sub["硬件成本（元）"], y=df_sub["创想总毛利（万元）"],
            name=f"创想-销量{vol}台",
            line=dict(color=colors[i % len(colors)], dash="dot"),
            yaxis="y2"
        ))
    fig_line.update_layout(
        xaxis_title="硬件成本（元）",
        yaxis_title="创维总毛利（万元）",
        yaxis2=dict(title="创想总毛利（万元）", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)

# 等高线热力图（创维）
with col_chart2:
    st.subheader("2. 等高线热力图（创维数字）")
    st.caption("X轴：硬件成本 | Y轴：销量 | 颜色深浅：毛利高低（绿=赚，红=亏）")
    fig_contour_skyworth = go.Figure(data=go.Contour(
        z=sensitivity_df["创维总毛利（万元）"],
        x=sensitivity_df["硬件成本（元）"],
        y=sensitivity_df["销量（台）"],
        colorscale="RdYlGn",
        colorbar=dict(title="创维总毛利（万元）"),
        contours=dict(showlabels=True)
    ))
    fig_contour_skyworth.update_layout(
        xaxis_title="硬件成本（元）",
        yaxis_title="销量（台）",
        height=500
    )
    st.plotly_chart(fig_contour_skyworth, use_container_width=True)

# 等高线热力图（创想）
col_chart3, _ = st.columns(2)
with col_chart3:
    st.subheader("3. 等高线热力图（创想悦动）")
    st.caption("X轴：硬件成本 | Y轴：销量 | 颜色深浅：毛利高低（绿=赚，红=亏）")
    fig_contour_youduo = go.Figure(data=go.Contour(
        z=sensitivity_df["创想总毛利（万元）"],
        x=sensitivity_df["硬件成本（元）"],
        y=sensitivity_df["销量（台）"],
        colorscale="RdYlGn",
        colorbar=dict(title="创想总毛利（万元）"),
        contours=dict(showlabels=True)
    ))
    fig_contour_youduo.update_layout(
        xaxis_title="硬件成本（元）",
        yaxis_title="销量（台）",
        height=500
    )
    st.plotly_chart(fig_contour_youduo, use_container_width=True)

# -------------------------- 5. 保存方案功能 --------------------------
st.divider()
col_save, _ = st.columns([1, 5])
with col_save:
    if st.button("💾 保存当前方案", type="primary"):
        st.session_state["show_plan_report"] = True

if st.session_state.get("show_plan_report", False):
    from datetime import datetime
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构建方案报告HTML
    def build_plan_html():
        # 套装价格表
        price_table = f"""
        <table style="width:100%;border-collapse:collapse;margin-bottom:15px;">
            <tr style="background:#1f77b4;color:white;">
                <th style="padding:8px;border:1px solid #ddd;">SKU</th>
                <th style="padding:8px;border:1px solid #ddd;">官方指导价（元）</th>
                <th style="padding:8px;border:1px solid #ddd;">大促价（元）</th>
            </tr>
            <tr><td style="padding:6px;border:1px solid #ddd;">标准版</td><td style="text-align:center;padding:6px;border:1px solid #ddd;">{std_guide_price}</td><td style="text-align:center;padding:6px;border:1px solid #ddd;">{std_promo_price}</td></tr>
            <tr><td style="padding:6px;border:1px solid #ddd;">家庭版</td><td style="text-align:center;padding:6px;border:1px solid #ddd;">{fam_guide_price}</td><td style="text-align:center;padding:6px;border:1px solid #ddd;">{fam_promo_price}</td></tr>
            <tr><td style="padding:6px;border:1px solid #ddd;">豪华版</td><td style="text-align:center;padding:6px;border:1px solid #ddd;">{lux_guide_price}</td><td style="text-align:center;padding:6px;border:1px solid #ddd;">{lux_promo_price}</td></tr>
        </table>"""
        
        # 赠品配置表
        gift_rows = ""
        for sku_name in sku_list:
            sc = sku_base_config[sku_name]
            gift_rows += f"""
            <tr>
                <td style="padding:6px;border:1px solid #ddd;font-weight:bold;">{sku_name}</td>
                <td style="text-align:center;padding:6px;border:1px solid #ddd;">{sc['default_extra_remote']}</td>
                <td style="text-align:center;padding:6px;border:1px solid #ddd;">{sc['default_light_gun']}</td>
                <td style="text-align:center;padding:6px;border:1px solid #ddd;">月卡×{sc['default_vip_month']} / 年卡×{sc['default_vip_year']}</td>
                <td style="text-align:center;padding:6px;border:1px solid #ddd;">{sc['default_parent_card']}</td>
                <td style="text-align:center;padding:6px;border:1px solid #ddd;">全套×{sc['default_nfc_full']} / SSR×{sc['default_nfc_ssr']}</td>
            </tr>"""
        gift_table = f"""
        <table style="width:100%;border-collapse:collapse;margin-bottom:15px;">
            <tr style="background:#ff7f0e;color:white;">
                <th style="padding:8px;border:1px solid #ddd;">SKU版本</th>
                <th style="padding:8px;border:1px solid #ddd;">额外遥控器</th>
                <th style="padding:8px;border:1px solid #ddd;">光枪</th>
                <th style="padding:8px;border:1px solid #ddd;">VIP卡</th>
                <th style="padding:8px;border:1px solid #ddd;">家长钥匙卡</th>
                <th style="padding:8px;border:1px solid #ddd;">NFC卡</th>
            </tr>
            {gift_rows}
        </table>"""
        
        # 渠道成本费率表
        ch_rate_rows = ""
        for ch in all_channel:
            ch_rate_rows += f"<tr><td style='padding:6px;border:1px solid #ddd;'>{ch}</td><td style='text-align:center;padding:6px;border:1px solid #ddd;'>{channel_rate_config[ch]}%</td><td style='text-align:center;padding:6px;border:1px solid #ddd;'>{channel_volume_dict[ch]:,}台</td></tr>"
        ch_rate_table = f"""
        <table style="width:100%;border-collapse:collapse;margin-bottom:15px;">
            <tr style="background:#2ca02c;color:white;">
                <th style='padding:8px;border:1px solid #ddd;'>渠道</th>
                <th style='padding:8px;border:1px solid #ddd;'>当前阶段费率({use_channel_stage})</th>
                <th style='padding:8px;border:1px solid #ddd;'>销量</th>
            </tr>
            {ch_rate_rows}
        </table>"""
        
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; padding: 30px; max-width: 1100px; margin: 0 auto; background: #fff; color: #333; }}
            h1 {{ text-align: center; color: #1f77b4; border-bottom: 3px solid #1f77b4; padding-bottom: 10px; }}
            .time {{ text-align: center; color: #888; margin-bottom: 20px; }}
            h2 {{ background: linear-gradient(90deg,#1f77b422,transparent); padding-left:10px; border-left:4px solid #1f77b4; color:#1f77b4; }}
            h3 {{ color:#555; margin-top:20px; border-bottom:1px solid #eee; }}
            .metric-row {{ display:flex; justify-content:space-around; flex-wrap:wrap; gap:10px; margin-bottom:20px; }}
            .metric-card {{ background:#f8f9fa; border-radius:8px; padding:12px 20px; text-align:center; min-width:150px; border:1px solid #e0e0e0; }}
            .metric-card .label {{ font-size:13px; color:#666; }}
            .metric-card .value {{ font-size:22px; font-weight:bold; margin:5px 0; }}
            .metric-card .sub {{ font-size:11px; color:#999; }}
            .green {{ color:#27ae60; }} .red {{ color:#e74c3c; }}
            table {{ font-size:14px; }}
            th, td {{ text-align:left; }}
            .param-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px 20px; }}
            .param-item {{ display:flex; justify-content:space-between; padding:6px 10px; background:#fafafa; border-radius:4px; border-left:3px solid #ff7f0e; font-size:14px; }}
            .param-name {{ color:#555; }} .param-val {{ font-weight:bold; color:#333; }}
        </style>
        </head>
        <body>
            <h1>🎮 YOUDOO BOX 毛利测算方案报告</h1>
            <p class='time'>⏰ 方案生成时间：{now} | 当前售价模式：{price_mode} | 渠道成本阶段：{use_channel_stage}</p>
            
            <!-- 核心指标 -->
            <h2>一、核心指标汇总</h2>
            <div class='metric-row'>
                <div class='metric-card'><div class='label'>总销量</div><div class='value'>{total_sales_volume:,}台</div><div class='sub'>均价 {round(avg_price_per,2)}元</div></div>
                <div class='metric-card'><div class='label'>渠道总成本</div><div class='value'>{round(total_channel_cost/10000,2)}万</div><div class='sub'>单台 {round(avg_channel_cost_per,2)}元</div></div>
                <div class='metric-card'><div class='label' class='green'>创维数字总毛利</div><div class='value {'green' if total_skyworth_profit>=0 else 'red'}'>{round(total_skyworth_profit/10000,2)}万元</div><div class='sub'>硬件:{round(total_skyworth_hardware_profit/10000,2)}万 续费:{round(total_skyworth_renew_profit/10000,2)}万</div></div>
                <div class='metric-card'><div class='label'>创想悦动总毛利</div><div class='value {'green' if total_youduo_profit>=0 else 'red'}'>{round(total_youduo_profit/10000,2)}万元</div><div class='sub'>硬件:{round(total_youduo_hardware_profit/10000,2)}万 续费:{round(total_youduo_renew_profit/10000,2)}万</div></div>
                <div class='metric-card'><div class='label'>产品总毛利</div><div class='value {'green' if total_profit>=0 else 'red'}'>{round(total_profit/10000,2)}万元</div><div class='sub'>毛利率 {total_margin_rate}%</div></div>
            </div>
            
            <!-- 套装价格表 -->
            <h2>二、套装价格配置</h2>
            {price_table}
            
            <!-- 赠品配置表 -->
            <h3>各套装赠品/配件配置</h3>
            {gift_table}
            
            <!-- 渠道销量与成本 -->
            <h2>三、渠道销量占比</h2>
            {ch_rate_table}
            
            <!-- SKU销量占比 -->
            <h3>SKU销量占比</h3>
            <div style='display:flex;gap:20px;margin-bottom:15px;font-size:14px;'>
                <div style='flex:1;background:#f0f8ff;padding:10px;border-radius:6px;'>
                    <strong>线上渠道：</strong>标准版占{online_standard_ratio}% ({online_standard_volume:,}台) / 家庭版占{online_family_ratio}% ({online_family_volume:,}台)
                </div>
                <div style='flex:1;background:#fff8f0;padding:10px;border-radius:6px;'>
                    <strong>线下渠道：</strong>家庭版占{offline_family_ratio}% ({offline_family_volume:,}台) / 豪华版占{offline_luxury_ratio}% ({offline_luxury_volume:,}台)
                </div>
            </div>
            
            <!-- 主要参数汇总 -->
            <h2>四、主要参数设置</h2>
            <div class='param-grid'>
                <div class='param-item'><span class='param-name'>基础硬件成本</span><span class='param-val'>{base_hardware_cost} 元</span></div>
                <div class='param-item'><span class='param-name'>单台版权费(创维→创想)</span><span class='param-val'>{royalty_fee} 元</span></div>
                <div class='param-item'><span class='param-name'>会员续费率</span><span class='param-val'>{renew_rate}%</span></div>
                <div class='param-item'><span class='param-name'>续费年卡价格</span><span class='param-val'>{renew_vip_year_price} 元</span></div>
                <div class='param-item'><span class='param-name'>续费月卡价格</span><span class='param-val'>{renew_vip_month_price} 元</span></div>
                <div class='param-item'><span class='param-name'>年卡续费占比</span><span class='param-val'>{year_card_renew_ratio}%</span></div>
                <div class='param-item'><span class='param-name'>会员收入创维分成比例</span><span class='param-val'>{vip_split_rate_pct}%</span></div>
                <div class='param-item'><span class='param-name'>赠送会员折价计提比例</span><span class='param-val'>{vip_discount_rate_pct}%</span></div>
                <div class='param-item'><span class='param-name'>单用户年均续费收入</span><span class='param-val'>{round(single_user_year_renew_revenue,2)} 元</span></div>
                <div class='param-item'><span class='param-name'>续费计算年限</span><span class='param-val'>{renew_years} 年</span></div>
            </div>
            
            <p style='text-align:center;color:#aaa;margin-top:40px;font-size:12px;'>— YOUDOO BOX 毛利测算财务模型 V6.4 自动生成 —</p>
        </body>
        </html>
        """
        return html
    
    plan_html = build_plan_html()
    
    # 显示预览
    st.subheader("📋 方案预览")
    st.components.v1.html(plan_html, height=900, scrolling=True)
    
    # 提供HTML下载
    st.download_button(
        label="📥 下载方案报告(HTML)",
        data=plan_html,
        file_name=f"YOUDOO_方案_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html"
    )