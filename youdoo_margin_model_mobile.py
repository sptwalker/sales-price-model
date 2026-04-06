import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import io
import os
import random
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 页面配置 - 手机版
# ============================================================
st.set_page_config(
    page_title="YOUDOO BOX 毛利模型 手机版",
    layout="centered",
    page_icon="🎮"
)

# ============================================================
# 随机方案名预设（水果+动物）
# ============================================================
SCHEME_NAME_LIST = [
    "草莓", "芒果", "蓝莓", "橙子", "蜜桃", "葡萄", "荔枝", "西瓜",
    "熊猫", "考拉", "小鹿", "松鼠", "兔子", "狐狸", "企鹅", "海豚"
]

# ============================================================
# 0. Session State 初始化
# ============================================================
if "jd_ratio" not in st.session_state:
    st.session_state.jd_ratio = 15
if "tmall_ratio" not in st.session_state:
    st.session_state.tmall_ratio = 15
if "douyin_ratio" not in st.session_state:
    st.session_state.douyin_ratio = 20
if "offline_ratio" not in st.session_state:
    st.session_state.offline_ratio = 50
if "online_standard_ratio" not in st.session_state:
    st.session_state.online_standard_ratio = 60
if "online_family_ratio" not in st.session_state:
    st.session_state.online_family_ratio = 40
if "offline_family_ratio" not in st.session_state:
    st.session_state.offline_family_ratio = 80
if "offline_luxury_ratio" not in st.session_state:
    st.session_state.offline_luxury_ratio = 20
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

# ============================================================
# 回调函数
# ============================================================
def on_channel_change(changed_key):
    keys = ["jd_ratio", "tmall_ratio", "douyin_ratio", "offline_ratio"]
    vals = {k: st.session_state[k] for k in keys}
    total = sum(vals.values())
    if total == 0:
        return
    delta = total - 100
    others = {k: vals[k] for k in keys if k != changed_key}
    others_total = sum(others.values())
    if others_total == 0:
        per = delta / len(others)
        for k in others:
            st.session_state[k] = max(0, min(100, others[k] - per))
    else:
        for k in others:
            ratio = others[k] / others_total
            st.session_state[k] = max(0, min(100, others[k] - delta * ratio))

def on_online_sku_change(changed_key):
    if changed_key == "online_standard_ratio":
        st.session_state.online_family_ratio = 100 - st.session_state.online_standard_ratio
    else:
        st.session_state.online_standard_ratio = 100 - st.session_state.online_family_ratio
    st.session_state.online_standard_ratio = max(0, min(100, st.session_state.online_standard_ratio))
    st.session_state.online_family_ratio = max(0, min(100, st.session_state.online_family_ratio))

def on_offline_sku_change(changed_key):
    if changed_key == "offline_family_ratio":
        st.session_state.offline_luxury_ratio = 100 - st.session_state.offline_family_ratio
    else:
        st.session_state.offline_family_ratio = 100 - st.session_state.offline_luxury_ratio
    st.session_state.offline_family_ratio = max(0, min(100, st.session_state.offline_family_ratio))
    st.session_state.offline_luxury_ratio = max(0, min(100, st.session_state.offline_luxury_ratio))

def adjust_price(key, delta):
    st.session_state[key] = max(1000, min(5000, st.session_state[key] + delta))

# ============================================================
# 1. 预设基础数据
# ============================================================
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

item_cost = {
    "remote": 120, "light_gun": 89, "vip_month": 49, "vip_year": 358,
    "parent_card": 49, "nfc_full": 49, "nfc_ssr": 99, "card_cost_rate": 0.2
}

# ============================================================
# 2. 侧边栏参数面板（保留原设计）
# ============================================================
st.sidebar.header("📊 全渠道销量与分配")
total_sales_volume = st.sidebar.slider("全渠道总销售总量（台）", 20000, 500000, 100000, step=10000)
st.sidebar.caption("✅ 渠道占比自动联动，总和永远100%")
jd_ratio = st.sidebar.slider("京东销量占比（%）", 0, 100, key="jd_ratio", on_change=on_channel_change, args=("jd_ratio",))
tmall_ratio = st.sidebar.slider("天猫销量占比（%）", 0, 100, key="tmall_ratio", on_change=on_channel_change, args=("tmall_ratio",))
douyin_ratio = st.sidebar.slider("抖音销量占比（%）", 0, 100, key="douyin_ratio", on_change=on_channel_change, args=("douyin_ratio",))
offline_ratio = st.sidebar.slider("线下销量占比（%）", 0, 100, key="offline_ratio", on_change=on_channel_change, args=("offline_ratio",))

st.sidebar.divider()
st.sidebar.header("💰 渠道成本费率设置（%）")
st.sidebar.caption("独立设置各渠道前期/后期成本占比")
price_mode = st.sidebar.radio("售价模式", ["官方指导价", "大促价"], index=1)
use_channel_stage = st.sidebar.radio("当前渠道成本阶段", ["前期", "后期"], index=0)

with st.sidebar.expander("各渠道成本费率", expanded=True):
    jd_rate = st.slider("京东前期（%）", 0, 80, key="jd_rate_early")
    jd_rate_l = st.slider("京东后期（%）", 0, 80, key="jd_rate_late")
    tmall_rate = st.slider("天猫前期（%）", 0, 80, key="tmall_rate_early")
    tmall_rate_l = st.slider("天猫后期（%）", 0, 80, key="tmall_rate_late")
    douyin_rate = st.slider("抖音前期（%）", 0, 80, key="douyin_rate_early")
    douyin_rate_l = st.slider("抖音后期（%）", 0, 80, key="douyin_rate_late")
    offline_rate = st.slider("线下前期（%）", 0, 80, key="offline_rate_early")
    offline_rate_l = st.slider("线下后期（%）", 0, 80, key="offline_rate_late")

channel_rate_config = {
    "京东": jd_rate if use_channel_stage == "前期" else jd_rate_l,
    "天猫": tmall_rate if use_channel_stage == "前期" else tmall_rate_l,
    "抖音": douyin_rate if use_channel_stage == "前期" else douyin_rate_l,
    "线下": offline_rate if use_channel_stage == "前期" else offline_rate_l
}

st.sidebar.divider()
st.sidebar.subheader("🎮 多SKU销量占比分配")
st.sidebar.caption("规则：线上仅售标准版/家庭版，线下仅售家庭版/豪华版 | 自动联动归一化")
online_standard_ratio = st.sidebar.slider("标准版线上占比（%）", 0, 100, key="online_standard_ratio", on_change=on_online_sku_change, args=("online_standard_ratio",))
online_family_ratio = st.sidebar.slider("家庭版线上占比（%）", 0, 100, key="online_family_ratio", on_change=on_online_sku_change, args=("online_family_ratio",))
offline_family_ratio = st.sidebar.slider("家庭版线下占比（%）", 0, 100, key="offline_family_ratio", on_change=on_offline_sku_change, args=("offline_family_ratio",))
offline_luxury_ratio = st.sidebar.slider("豪华版线下占比（%）", 0, 100, key="offline_luxury_ratio", on_change=on_offline_sku_change, args=("offline_luxury_ratio",))

st.sidebar.divider()
st.sidebar.header("📦 产品套装价格设定")

def sidebar_price_control(key, label, min_val, max_val):
    st.sidebar.markdown(f"**▸ {label}**")
    price_val = st.sidebar.slider("", min_val, max_val, key=key)
    return price_val

std_guide_price = sidebar_price_control("std_guide", "标准版官方指导价", 1500, 2500)
std_promo_price = sidebar_price_control("std_promo", "标准版大促价", 1400, 2400)
st.sidebar.markdown("---")
fam_guide_price = sidebar_price_control("fam_guide", "家庭版官方指导价", 1800, 2800)
fam_promo_price = sidebar_price_control("fam_promo", "家庭版大促价", 1700, 2700)
st.sidebar.markdown("---")
lux_guide_price = sidebar_price_control("lux_guide", "豪华版官方指导价", 2200, 3500)
lux_promo_price = sidebar_price_control("lux_promo", "豪华版大促价", 2100, 3400)

sku_price_config = {
    "标准版": {"guide_price": std_guide_price, "promo_price": std_promo_price},
    "家庭版": {"guide_price": fam_guide_price, "promo_price": fam_promo_price},
    "豪华版": {"guide_price": lux_guide_price, "promo_price": lux_promo_price}
}

st.sidebar.divider()
st.sidebar.header("🎁 套装赠品/附件配置")
selected_sku = st.sidebar.selectbox("选择要配置的套装", sku_list)
sku_default = sku_base_config[selected_sku]
st.sidebar.markdown(f"**▸ {selected_sku} 赠品数量配置**")
c_g1, c_g2 = st.sidebar.columns(2)
with c_g1:
    extra_remote = st.sidebar.number_input("额外遥控器数量", 0, 10, sku_default["default_extra_remote"])
    light_gun = st.sidebar.number_input("光枪数量", 0, 10, sku_default["default_light_gun"])
    vip_month = st.sidebar.number_input("VIP月卡数量", 0, 24, sku_default["default_vip_month"])
    vip_year = st.sidebar.number_input("VIP年卡数量", 0, 10, sku_default["default_vip_year"])
with c_g2:
    parent_card = st.sidebar.number_input("家长钥匙卡数量", 0, 5, sku_default["default_parent_card"])
    nfc_full = st.sidebar.number_input("NFC全套卡数量", 0, 5, sku_default["default_nfc_full"])
    nfc_ssr = st.sidebar.number_input("NFC SSR卡数量", 0, 5, sku_default["default_nfc_ssr"])
sku_base_config[selected_sku].update({
    "default_extra_remote": extra_remote,
    "default_light_gun": light_gun,
    "default_vip_month": vip_month,
    "default_vip_year": vip_year,
    "default_parent_card": parent_card,
    "default_nfc_full": nfc_full,
    "default_nfc_ssr": nfc_ssr
})

st.sidebar.divider()
st.sidebar.header("📅 会员续费收入设置")
st.sidebar.caption("赠送会员到期后，用户主动续费的收入计算")
c_v1, c_v2 = st.sidebar.columns(2)
with c_v1:
    renew_vip_year_price = st.sidebar.slider("续费年卡价格（元）", 200, 500, 358)
    renew_rate = st.sidebar.slider("会员续费率（%）", 10, 90, 60, format="%d%%")
with c_v2:
    renew_vip_month_price = st.sidebar.slider("续费月卡价格（元）", 20, 80, 49)
    year_card_renew_ratio = st.sidebar.slider("年卡续费占比（%）", 0, 100, 80, format="%d%%")
renew_years = 1

st.sidebar.divider()
st.sidebar.subheader("💰 其他分账与成本参数")
royalty_fee = st.sidebar.slider("单台版权费（创维→创想，元）", 100, 300, 200)
vip_split_rate_pct = st.sidebar.slider("会员收入创维分成比例", 0, 50, 20, format="%d%%")
vip_split_rate = vip_split_rate_pct / 100
vip_discount_rate_pct = st.sidebar.slider("赠送会员折价计提比例", 0, 100, 50, format="%d%%")
vip_discount_rate = vip_discount_rate_pct / 100
base_hardware_cost = st.sidebar.number_input("基础硬件成本（含标配/运输/售后，元）", value=984)

# ============================================================
# 3. 核心财务计算
# ============================================================
channel_volume_dict = {
    "京东": int(total_sales_volume * jd_ratio / 100),
    "天猫": int(total_sales_volume * tmall_ratio / 100),
    "抖音": int(total_sales_volume * douyin_ratio / 100),
    "线下": total_sales_volume - int(total_sales_volume * jd_ratio / 100) - int(total_sales_volume * tmall_ratio / 100) - int(total_sales_volume * douyin_ratio / 100)
}
online_total_volume = sum(channel_volume_dict[ch] for ch in online_channel)
offline_total_volume = channel_volume_dict["线下"]

online_standard_volume = int(online_total_volume * online_standard_ratio / 100)
online_family_volume = online_total_volume - online_standard_volume
offline_family_volume = int(offline_total_volume * offline_family_ratio / 100)
offline_luxury_volume = offline_total_volume - offline_family_volume

sku_total_volume = {
    "标准版": online_standard_volume,
    "家庭版": online_family_volume + offline_family_volume,
    "豪华版": offline_luxury_volume
}

sku_calc_detail = {}
total_skyworth_hardware_profit = 0
total_youduo_hardware_profit = 0
total_revenue = 0
total_channel_cost = 0
total_p_hw = total_p_sw = total_c_hw_base = total_c_hw_extra = 0
total_r_royalty = total_s_split = total_c_card = total_c_vip_discount = 0
sku_sales_amount = {}
sku_sales_cost = {}

for sku in sku_list:
    sku_config = sku_base_config[sku]
    sku_vol = sku_total_volume[sku]
    if sku_vol == 0:
        continue
    sku_price = sku_price_config[sku]["guide_price"] if price_mode == "官方指导价" else sku_price_config[sku]["promo_price"]
    sku_online_vol = online_standard_volume if sku == "标准版" else (online_family_volume if sku == "家庭版" else 0)
    sku_offline_vol = 0 if sku == "标准版" else (offline_family_volume if sku == "家庭版" else offline_luxury_volume)
    sku_total_vol = sku_online_vol + sku_offline_vol
    if sku_total_vol > 0:
        online_rate_total = sum(channel_rate_config[ch] * (channel_volume_dict[ch] / online_total_volume) for ch in online_channel if online_total_volume > 0)
        avg_channel_rate = (online_rate_total * sku_online_vol + channel_rate_config["线下"] * sku_offline_vol) / sku_total_vol
        avg_channel_cost_per = sku_price * avg_channel_rate / 100
    else:
        avg_channel_rate = avg_channel_cost_per = 0
    extra_hardware_cost = sku_config["default_extra_remote"] * item_cost["remote"] + sku_config["default_light_gun"] * item_cost["light_gun"]
    vip_total_price = sku_config["default_vip_month"] * item_cost["vip_month"] + sku_config["default_vip_year"] * item_cost["vip_year"]
    card_total_price = sku_config["default_parent_card"] * item_cost["parent_card"] + sku_config["default_nfc_full"] * item_cost["nfc_full"] + sku_config["default_nfc_ssr"] * item_cost["nfc_ssr"]
    p_hw_per = sku_price - vip_total_price - card_total_price
    p_sw_per = vip_total_price + card_total_price
    card_cost_per = card_total_price * item_cost["card_cost_rate"]
    vip_discount_cost_per = vip_total_price * vip_discount_rate
    s_split_per = vip_total_price * vip_split_rate
    skyworth_profit_per = p_hw_per + s_split_per - base_hardware_cost - extra_hardware_cost - avg_channel_cost_per - royalty_fee
    youduo_profit_per = p_sw_per + royalty_fee - s_split_per - card_cost_per - vip_discount_cost_per
    sku_sales_amount[sku] = sku_price * sku_vol
    sku_sales_cost[sku] = (base_hardware_cost + extra_hardware_cost + avg_channel_cost_per) * sku_vol
    sku_calc_detail[sku] = {
        "销量": f"{sku_vol:,}台", "售价": f"¥{sku_price}", "渠道费率": f"{round(avg_channel_rate, 1)}%",
        "创维单台毛利": f"¥{round(skyworth_profit_per, 0)}", "创想单台毛利": f"¥{round(youduo_profit_per, 0)}"
    }
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

month_card_renew_ratio = 1 - year_card_renew_ratio / 100
single_user_year_renew_revenue = (renew_rate / 100) * ((year_card_renew_ratio / 100) * renew_vip_year_price + month_card_renew_ratio * renew_vip_month_price * 12)
total_renew_revenue = total_sales_volume * single_user_year_renew_revenue * renew_years
total_skyworth_renew_profit = total_renew_revenue * vip_split_rate
total_youduo_renew_profit = total_renew_revenue * (1 - vip_split_rate)
total_skyworth_profit = total_skyworth_hardware_profit + total_skyworth_renew_profit
total_youduo_profit = total_youduo_hardware_profit + total_youduo_renew_profit
total_profit = total_skyworth_profit + total_youduo_profit
avg_price_per = total_revenue / total_sales_volume if total_sales_volume > 0 else 0
avg_channel_cost_per_total = total_channel_cost / total_sales_volume if total_sales_volume > 0 else 0
avg_channel_rate = avg_channel_cost_per_total / avg_price_per * 100 if avg_price_per > 0 else 0
total_margin_rate = round(total_profit / (total_revenue + total_renew_revenue) * 100, 2) if (total_revenue + total_renew_revenue) > 0 else 0

# Plotly 图表配置：禁用所有触摸交互
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
    "doubleClick": False,
    "dragmode": False,
    "modeBarButtonsToRemove": ["zoomIn2d", "zoomOut2d", "pan2d", "lasso2d", "select2d", "autoScale2d", "resetScale2d"]
}

# ============================================================
# 4. 主界面 - 手机版展示
# ============================================================
st.title("🎮 YOUDOO BOX 产品毛利测算模型 V6.7 手机版")
st.caption("✅ 销量-会员收入-毛利强关联修正 | 硬件/续费毛利拆分展示")

st.divider()

# --- 核心指标：手机端2列卡片 ---
st.subheader("📊 核心指标")
st.metric("全渠道总销售额", f"¥{round(total_revenue/10000, 1)} 万元", f"全渠道总销量 {total_sales_volume:,} 台 | 均价 ¥{round(avg_price_per, 0)}")
c1, c2 = st.columns(2)
with c1:
    st.metric("全渠道总销量", f"{total_sales_volume:,} 台", f"均价 ¥{round(avg_price_per, 0)}")
with c2:
    st.metric("渠道综合成本", f"{round(total_channel_cost/10000, 1)} 万元", f"单台 ¥{round(avg_channel_cost_per_total, 0)}")

c3, c4 = st.columns(2)
with c3:
    st.metric("创维数字总毛利", f"{round(total_skyworth_profit/10000, 1)} 万元",
              f"硬件 {round(total_skyworth_hardware_profit/10000, 1)}万 | 续费 {round(total_skyworth_renew_profit/10000, 1)}万")
with c4:
    st.metric("创想悦动总毛利", f"{round(total_youduo_profit/10000, 1)} 万元",
              f"硬件 {round(total_youduo_hardware_profit/10000, 1)}万 | 续费 {round(total_youduo_renew_profit/10000, 1)}万")

c5, _ = st.columns([1, 2])
with c5:
    st.metric("产品总毛利", f"{round(total_profit/10000, 1)} 万元",
              f"综合毛利率 {total_margin_rate}%")

# --- 续费联动说明 ---
st.markdown(f"""
**📈 销量-会员续费联动校验**

- 总续费用户基数：**{total_sales_volume:,} 台**（与总销量完全绑定）
- 单用户年均续费收入：**¥{round(single_user_year_renew_revenue, 2)}**
- {renew_years}年累计续费总收入：**{round(total_renew_revenue/10000, 2)} 万元**
- 销量涨10倍 → 续费收入同步涨10倍
""")

st.divider()

# --- SKU毛利明细 - 手机友好表格 ---
st.subheader("🎮 各SKU销量与毛利明细")
sku_df = pd.DataFrame.from_dict(sku_calc_detail, orient="index").reset_index().rename(columns={"index": "SKU"})
st.dataframe(sku_df, use_container_width=True, hide_index=True)

# --- 饼图：2列布局 ---
st.divider()
st.subheader("📊 销售金额 vs 成本占比")
c_p1, c_p2 = st.columns(2)
with c_p1:
    if sku_sales_amount:
        fig1 = px.pie(names=list(sku_sales_amount.keys()), values=[v/10000 for v in sku_sales_amount.values()],
                      title="销售金额（万元）", hole=0.4)
        fig1.update_layout(height=350, font_size=13, title_font_size=14, margin=dict(t=40, b=10))
        st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)
with c_p2:
    if sku_sales_cost:
        fig2 = px.pie(names=list(sku_sales_cost.keys()), values=[v/10000 for v in sku_sales_cost.values()],
                      title="销售成本（万元）", hole=0.4)
        fig2.update_layout(height=350, font_size=13, title_font_size=14, margin=dict(t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

# --- 渠道成本明细 ---
st.divider()
st.subheader("📊 全渠道成本明细")
all_ch = online_channel + ["线下"]
ch_detail = []
for ch in all_ch:
    ch_vol = channel_volume_dict[ch]
    ch_rate = channel_rate_config[ch]
    if ch in online_channel:
        ch_avg_price = (std_promo_price * online_standard_volume + fam_promo_price * online_family_volume) / online_total_volume if online_total_volume > 0 else 0
    else:
        ch_avg_price = (fam_promo_price * offline_family_volume + lux_promo_price * offline_luxury_volume) / offline_total_volume if offline_total_volume > 0 else 0
    ch_cost_per = ch_avg_price * ch_rate / 100
    ch_detail.append({
        "渠道": ch, "销量": f"{ch_vol:,}台", "费率": f"{ch_rate}%",
        "单台成本": f"¥{round(ch_cost_per, 0)}", "总成本": f"{round(ch_vol * ch_cost_per / 10000, 2)}万元"
    })
ch_df = pd.DataFrame(ch_detail)
st.dataframe(ch_df, use_container_width=True, hide_index=True)
st.metric("渠道总成本合计", f"{round(total_channel_cost/10000, 2)} 万元", f"综合费率 {round(avg_channel_rate, 2)}%")

# --- 桑基图：高度缩减 ---
st.divider()
st.subheader("💸 加权平均单台资金流向图")
avg_p_hw_per = total_p_hw / total_sales_volume if total_sales_volume > 0 else 0
avg_p_sw_per = total_p_sw / total_sales_volume if total_sales_volume > 0 else 0
avg_c_hw_base_per = total_c_hw_base / total_sales_volume if total_sales_volume > 0 else 0
avg_c_hw_extra_per = total_c_hw_extra / total_sales_volume if total_sales_volume > 0 else 0
avg_r_royalty_per = total_r_royalty / total_sales_volume if total_sales_volume > 0 else 0
avg_s_split_per = total_s_split / total_sales_volume if total_sales_volume > 0 else 0
avg_c_card_per = total_c_card / total_sales_volume if total_sales_volume > 0 else 0
avg_c_vip_discount_per = total_c_vip_discount / total_sales_volume if total_sales_volume > 0 else 0
avg_sky_hw_per = total_skyworth_hardware_profit / total_sales_volume if total_sales_volume > 0 else 0
avg_you_hw_per = total_youduo_hardware_profit / total_sales_volume if total_sales_volume > 0 else 0

sankey_labels = ["消费者支付", "渠道成本", "创维收入", "创想收入", "硬件成本", "配件成本", "版权费", "创维毛利", "会员分成", "卡件成本", "折价成本", "创想毛利"]
sankey_source = [0, 0, 0, 2, 2, 2, 2, 8, 6, 3, 3, 3]
sankey_target = [1, 2, 3, 4, 5, 6, 7, 2, 3, 8, 9, 11]
sankey_values = [
    avg_channel_cost_per_total, avg_p_hw_per, avg_p_sw_per,
    avg_c_hw_base_per, avg_c_hw_extra_per, avg_r_royalty_per, max(avg_sky_hw_per, 0),
    avg_s_split_per, avg_r_royalty_per, avg_s_split_per, avg_c_card_per, max(avg_you_hw_per, 0)
]
fig_sankey = go.Figure(go.Sankey(
    node=dict(pad=12, thickness=18, line=dict(color="#333", width=0.5),
              label=sankey_labels,
              color=["#4A90D9", "#E74C3C", "#F39C12", "#27AE60", "#E74C3C", "#E74C3C", "#9B59B6", "#2ECC71", "#9B59B6", "#E74C3C", "#E74C3C", "#2ECC71"]),
    link=dict(source=sankey_source, target=sankey_target, value=sankey_values, color=["rgba(231,76,60,0.3)"]*12)
))
fig_sankey.update_layout(title_text="单台资金流向（单位：元）", font_size=12, height=380, dragmode=False)
st.plotly_chart(fig_sankey, use_container_width=True, config=PLOTLY_CONFIG)

# --- 敏感性分析 ---
st.divider()
st.subheader("📈 敏感性分析（硬件成本 × 销量 对毛利的影响）")
hw_range = np.linspace(base_hardware_cost - 100, base_hardware_cost + 100, 6)
vol_levels = [50000, 100000, 200000, 300000, 500000]
sens_data = []
for vol in vol_levels:
    for hw in hw_range:
        sky_hw = avg_p_hw_per + avg_s_split_per - hw - avg_c_hw_extra_per - avg_channel_cost_per_total - royalty_fee
        you_hw = avg_p_sw_per + royalty_fee - avg_s_split_per - avg_c_card_per - avg_c_vip_discount_per
        renew = vol * single_user_year_renew_revenue * renew_years
        sky_r = renew * vip_split_rate
        you_r = renew * (1 - vip_split_rate)
        sens_data.append({
            "硬件成本（元）": hw, "销量（台）": vol,
            "创维总毛利（万元）": (sky_hw * vol + sky_r) / 10000,
            "创想总毛利（万元）": (you_hw * vol + you_r) / 10000
        })
sens_df = pd.DataFrame(sens_data)
colors = px.colors.qualitative.Set2

# 折线图1：创维总毛利
fig_s1 = go.Figure()
for i, vol in enumerate(vol_levels):
    sub = sens_df[sens_df["销量（台）"] == vol]
    fig_s1.add_trace(go.Scatter(x=sub["硬件成本（元）"], y=sub["创维总毛利（万元）"],
                                name=f"创维-{int(vol/1000)}k",
                                line=dict(color=colors[i % len(colors)])))
fig_s1.update_layout(title="折线图：硬件成本 vs 创维总毛利", xaxis_title="硬件成本（元）",
                     yaxis_title="创维总毛利（万元）", height=350,
                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                     dragmode=False)
st.plotly_chart(fig_s1, use_container_width=True, config=PLOTLY_CONFIG)

# 折线图2：创想总毛利
fig_s2 = go.Figure()
for i, vol in enumerate(vol_levels):
    sub = sens_df[sens_df["销量（台）"] == vol]
    fig_s2.add_trace(go.Scatter(x=sub["硬件成本（元）"], y=sub["创想总毛利（万元）"],
                                name=f"创想-{int(vol/1000)}k",
                                line=dict(color=colors[i % len(colors)], dash="dot")))
fig_s2.update_layout(title="折线图：硬件成本 vs 创想总毛利", xaxis_title="硬件成本（元）",
                     yaxis_title="创想总毛利（万元）", height=350,
                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                     dragmode=False)
st.plotly_chart(fig_s2, use_container_width=True, config=PLOTLY_CONFIG)

# 热力图1：创维数字
st.subheader("🌡️ 等高线热力图（创维数字）")
st.caption("X轴：硬件成本 | Y轴：销量 | 颜色深浅：毛利高低（绿=赚，红=亏）")
fig_contour_sky = go.Figure(data=go.Contour(
    z=sens_df["创维总毛利（万元）"],
    x=sens_df["硬件成本（元）"],
    y=sens_df["销量（台）"],
    colorscale="RdYlGn",
    colorbar=dict(title="创维总毛利（万元）"),
    contours=dict(showlabels=True)
))
fig_contour_sky.update_layout(xaxis_title="硬件成本（元）", yaxis_title="销量（台）",
                              height=400, dragmode=False)
st.plotly_chart(fig_contour_sky, use_container_width=True, config=PLOTLY_CONFIG)

# 热力图2：创想悦动
st.subheader("🌡️ 等高线热力图（创想悦动）")
st.caption("X轴：硬件成本 | Y轴：销量 | 颜色深浅：毛利高低（绿=赚，红=亏）")
fig_contour_you = go.Figure(data=go.Contour(
    z=sens_df["创想总毛利（万元）"],
    x=sens_df["硬件成本（元）"],
    y=sens_df["销量（台）"],
    colorscale="RdYlGn",
    colorbar=dict(title="创想总毛利（万元）"),
    contours=dict(showlabels=True)
))
fig_contour_you.update_layout(xaxis_title="硬件成本（元）", yaxis_title="销量（台）",
                              height=400, dragmode=False)
st.plotly_chart(fig_contour_you, use_container_width=True, config=PLOTLY_CONFIG)

# --- 财务明细 ---
st.divider()
st.subheader("📋 双主体财务明细（创维/创想）")
c_d1, c_d2 = st.columns(2)
with c_d1:
    st.markdown("**创维数字**")
    sky_df = pd.DataFrame({
        "项目": ["硬件收入", "会员分成", "续费分成", "硬件成本", "配件成本", "渠道成本", "版权费", "总毛利"],
        "万元": [round(total_p_hw/10000, 2), round(total_s_split/10000, 2), round(total_skyworth_renew_profit/10000, 2),
                round(-total_c_hw_base/10000, 2), round(-total_c_hw_extra/10000, 2),
                round(-total_channel_cost/10000, 2), round(-total_r_royalty/10000, 2), round(total_skyworth_profit/10000, 2)]
    })
    st.dataframe(sky_df, use_container_width=True, hide_index=True)
with c_d2:
    st.markdown("**创想悦动**")
    you_df = pd.DataFrame({
        "项目": ["软件服务", "版权费收入", "续费服务", "会员分成", "卡件成本", "折价成本", "总毛利"],
        "万元": [round(total_p_sw/10000, 2), round(total_r_royalty/10000, 2), round(total_youduo_renew_profit/10000, 2),
                round(-(total_s_split + total_skyworth_renew_profit)/10000, 2),
                round(-total_c_card/10000, 2), round(-total_c_vip_discount/10000, 2), round(total_youduo_profit/10000, 2)]
    })
    st.dataframe(you_df, use_container_width=True, hide_index=True)

# ============================================================
# 【中文乱码修复版】纯静态PNG方案信息图生成
# ============================================================
st.divider()
st.subheader("💾 保存当前方案")

# 中文兼容字体加载函数（核心修复）
def load_chinese_font(font_type="regular", font_size=18):
    font_paths = []
    if font_type == "bold":
        font_paths.append("NotoSansSC-Bold.ttf")
    else:
        font_paths.append("Lenovosmallhei.ttf")
    font_paths.append("C:/Windows/Fonts/msyh.ttc")
    font_paths.append("C:/Windows/Fonts/simhei.ttf")
    font_paths.append("/System/Library/Fonts/PingFang.ttc")
    font_paths.append("/System/Library/Fonts/STHeiti Light.ttc")
    font_paths.append("/usr/share/fonts/truetype/noto/Lenovosmallhei.ttf")
    font_paths.append("/usr/share/fonts/opentype/noto/Lenovosmallhei.ttf")
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
    return ImageFont.load_default(size=font_size)

# 文字换行函数
def wrap_text(text, font, max_width, draw):
    """将文字拆分为不超过 max_width 宽度的多行"""
    if not text:
        return [""]
    lines = []
    # 按竖线先拆大片断
    segments = text.split(" | ")
    current_line = ""
    for seg in segments:
        seg = seg.strip()
        test_line = current_line + (" | " if current_line else "") + seg
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_w = bbox[2] - bbox[0]
        if test_w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            # 如果单个seg本身就超宽，按字符继续拆
            current_line = seg
            bbox = draw.textbbox((0, 0), current_line, font=font)
            while bbox[2] - bbox[0] > max_width and len(current_line) > 1:
                # 从末尾往前砍到刚好塞下
                current_line = current_line[:-1]
                bbox = draw.textbbox((0, 0), current_line + "…", font=font)
                if bbox[2] - bbox[0] <= max_width:
                    break
            # 剩余部分重新处理
            remaining = seg[len(current_line):] if current_line == seg else seg[len(current_line):]
            while remaining:
                bbox = draw.textbbox((0, 0), remaining, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    current_line = remaining
                    remaining = ""
                else:
                    # 从前往后截
                    tmp = remaining
                    while len(tmp) > 1:
                        bbox = draw.textbbox((0, 0), tmp, font=font)
                        if bbox[2] - bbox[0] <= max_width:
                            break
                        tmp = tmp[:-1]
                    lines.append(tmp)
                    remaining = remaining[len(tmp):]
    if current_line:
        lines.append(current_line)
    return lines if lines else [""]

# 图片生成函数
def create_scheme_image(scheme_name, now, price_mode, use_channel_stage):
    # 图片基础配置
    img_width = 720  # 手机竖屏宽度
    row_height = 40   # 每行高度
    title_row_height = 50  # 区块标题行高度
    header_height = 80  # 顶部主标题高度
    footer_height = 60  # 底部备注高度
    margin = 40  # 左右边距

    # 构建所有内容行
    content_rows = []
    # 区块1：核心指标
    content_rows.append({"type": "title", "text": "📊 核心指标", "bg_color": "#4A90D9", "text_color": "white"})
    # 普通指标行（黑色）
    content_rows.append({"type": "content", "text": f"全渠道总销售额：¥{round(total_revenue/10000, 1)} 万元", "bg_color": "#F0F8FF"})
    content_rows.append({"type": "content", "text": f"全渠道总销量：{total_sales_volume:,} 台  |  单台均价 ¥{round(avg_price_per, 0)}", "bg_color": "white"})
    content_rows.append({"type": "content", "text": f"渠道综合成本：¥{round(total_channel_cost/10000, 1)} 万元  |  综合费率 {round(avg_channel_rate, 2)}%", "bg_color": "#F0F8FF"})
    # 毛利指标行（带颜色数字）
    sky_color = (0, 150, 70) if total_skyworth_profit >= 0 else (200, 50, 50)
    you_color = (0, 150, 70) if total_youduo_profit >= 0 else (200, 50, 50)
    tot_color = (0, 150, 70) if total_profit >= 0 else (200, 50, 50)
    content_rows.append({"type": "content_mv", "label": "创维数字总毛利", "value": f"¥{round(total_skyworth_profit/10000, 1)} 万元", "delta": f"硬件 {round(total_skyworth_hardware_profit/10000, 1)}万  续费 {round(total_skyworth_renew_profit/10000, 1)}万", "value_color": sky_color, "bg_color": "white"})
    content_rows.append({"type": "content_mv", "label": "创想悦动总毛利", "value": f"¥{round(total_youduo_profit/10000, 1)} 万元", "delta": f"硬件 {round(total_youduo_hardware_profit/10000, 1)}万  续费 {round(total_youduo_renew_profit/10000, 1)}万", "value_color": you_color, "bg_color": "#F0F8FF"})
    content_rows.append({"type": "content_mv", "label": "产品总毛利", "value": f"¥{round(total_profit/10000, 1)} 万元", "delta": f"综合毛利率 {total_margin_rate}%", "value_color": tot_color, "bg_color": "white"})
    
    # 区块2：各套装定价方案
    content_rows.append({"type": "title", "text": "📦 各套装定价方案", "bg_color": "#27AE60", "text_color": "white"})
    content_rows.append({"type": "content", "text": f"标准版：官方指导价 ¥{std_guide_price} | 大促价 ¥{std_promo_price}", "bg_color": "#F0F8FF"})
    content_rows.append({"type": "content", "text": f"家庭版：官方指导价 ¥{fam_guide_price} | 大促价 ¥{fam_promo_price}", "bg_color": "white"})
    content_rows.append({"type": "content", "text": f"豪华版：官方指导价 ¥{lux_guide_price} | 大促价 ¥{lux_promo_price}", "bg_color": "#F0F8FF"})
    
    # 区块3：各SKU详细配置方案（表格形式）
    content_rows.append({"type": "title", "text": "🎁 各SKU详细配置方案", "bg_color": "#F39C12", "text_color": "white"})
    # 表格头
    content_rows.append({
        "type": "table",
        "headers": ["SKU", "遥控器", "光枪", "VIP月卡", "VIP年卡", "家长卡", "NFC全套", "NFC SSR"],
        "rows": [
            [sku_name] + [
                str(sku_base_config[sku_name]["default_extra_remote"]),
                str(sku_base_config[sku_name]["default_light_gun"]),
                str(sku_base_config[sku_name]["default_vip_month"]),
                str(sku_base_config[sku_name]["default_vip_year"]),
                str(sku_base_config[sku_name]["default_parent_card"]),
                str(sku_base_config[sku_name]["default_nfc_full"]),
                str(sku_base_config[sku_name]["default_nfc_ssr"]),
            ]
            for sku_name in sku_list
        ],
        "bg_color": "#FFFFFF",
        "header_bg": "#F39C12",
    })
    
    # 区块4：会员价格方案
    content_rows.append({"type": "title", "text": "📋 会员价格方案", "bg_color": "#9B59B6", "text_color": "white"})
    content_rows.append({"type": "content", "text": f"会员年卡价格：¥{renew_vip_year_price}", "bg_color": "#F0F8FF"})
    content_rows.append({"type": "content", "text": f"会员月卡价格：¥{renew_vip_month_price}", "bg_color": "white"})
    
    # 区块5：详细销售参数设定
    content_rows.append({"type": "title", "text": "🔍 详细销售参数设定", "bg_color": "#888888", "text_color": "white"})
    content_rows.append({"type": "content", "text": f"渠道参数：京东 {channel_rate_config['京东']}%/{channel_volume_dict['京东']:,}台 | 天猫 {channel_rate_config['天猫']}%/{channel_volume_dict['天猫']:,}台 | 抖音 {channel_rate_config['抖音']}%/{channel_volume_dict['抖音']:,}台 | 线下 {channel_rate_config['线下']}%/{channel_volume_dict['线下']:,}台", "bg_color": "#F5F5F5"})
    content_rows.append({"type": "content", "text": f"硬件参数：基础硬件成本 ¥{base_hardware_cost} | 单台版权费 ¥{royalty_fee}", "bg_color": "#F5F5F5"})
    content_rows.append({"type": "content", "text": f"会员参数：会员续费率 {renew_rate}% | 年卡续费占比 {year_card_renew_ratio}% | 创维分成比例 {vip_split_rate_pct}% | 赠送会员折价比例 {vip_discount_rate_pct}%", "bg_color": "#F5F5F5"})

    # 加载字体
    font_main_title = load_chinese_font("bold", 24)
    font_title = load_chinese_font("bold", 20)
    font_content = load_chinese_font("regular", 18)
    font_footer = load_chinese_font("regular", 14)
    max_text_width = img_width - 2 * margin - 30

    # 第一次创建临时画布，用于计算换行后的真实高度
    temp_img = Image.new("RGB", (img_width, 10000), "white")
    temp_draw = ImageDraw.Draw(temp_img)

    # 计算每行换行后需要的总高度
    total_row_height = 0
    table_row_heights = []  # 记录每张表每行高度
    for row in content_rows:
        if row["type"] == "title":
            total_row_height += title_row_height
        elif row["type"] == "table":
            # 表格：1行表头 + N行数据，每行高38px
            n_data_rows = len(row["rows"])
            rh = (n_data_rows + 1) * 38
            total_row_height += rh
            table_row_heights.append(rh)
        elif row["type"] == "content_mv":
            # 毛利指标行：固定一行高度
            total_row_height += row_height
        else:
            wrapped = wrap_text(row["text"], font_content, max_text_width, temp_draw)
            total_row_height += max(len(wrapped) * row_height, row_height)
    img_height = header_height + total_row_height + footer_height

    # 创建正确高度的画布
    image = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(image)

    # 绘制顶部主标题
    main_title = f"YOUDOO BOX售价测算方案（{scheme_name}版）"
    draw.rectangle([0, 0, img_width, header_height], fill="#2C3E50")
    title_bbox = draw.textbbox((0, 0), main_title, font=font_main_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((img_width - title_w)/2, 26), main_title, font=font_main_title, fill="white")

    # 绘制内容行
    current_y = header_height
    table_idx = 0
    for row in content_rows:
        if row["type"] == "title":
            # 绘制标题行
            rh = title_row_height
            pad_y = 13  # 固定顶部内边距
            draw.rectangle([margin, current_y, img_width - margin, current_y + rh], fill=row["bg_color"])
            draw.text((margin + 15, current_y + pad_y), row["text"], font=font_title, fill="white")
            current_y += rh

        elif row["type"] == "table":
            # 绘制表格
            num_cols = len(row["headers"])
            col_w = (img_width - 2 * margin) / num_cols
            row_h = 38
            cell_pad_x = 8
            cell_pad_y = 9

            # 表头行
            rh = row_h
            draw.rectangle([margin, current_y, img_width - margin, current_y + rh], fill=row["header_bg"])
            for ci, hdr in enumerate(row["headers"]):
                cx = margin + ci * col_w
                bbox = draw.textbbox((0, 0), hdr, font=font_content)
                tw = bbox[2] - bbox[0]
                tx = cx + (col_w - tw) / 2
                ty = current_y + cell_pad_y
                draw.text((tx, ty), hdr, font=font_content, fill="white")
            current_y += rh

            # 数据行
            for ri, data_row in enumerate(row["rows"]):
                bg = "#FFF8E8" if ri % 2 == 0 else "#FFFFFF"
                draw.rectangle([margin, current_y, img_width - margin, current_y + row_h], fill=bg)
                for ci, val in enumerate(data_row):
                    cx = margin + ci * col_w
                    bbox = draw.textbbox((0, 0), str(val), font=font_content)
                    tw = bbox[2] - bbox[0]
                    tx = cx + (col_w - tw) / 2
                    ty = current_y + cell_pad_y
                    draw.text((tx, ty), str(val), font=font_content, fill="#333333")
                current_y += row_h

        elif row["type"] == "content_mv":
            # 毛利指标行：左侧标签 + 中间彩色数值 + 右侧小字
            rh = row_height
            pad_y = 14  # 文字顶部边距（稍大一些，往下调）
            label_text = row["label"]
            value_text = row["value"]
            delta_text = row.get("delta", "")
            value_color = row.get("value_color", "#000000")
            content_w = img_width - 2 * margin - 30  # 可用宽度

            draw.rectangle([margin, current_y, img_width - margin, current_y + rh], fill=row["bg_color"])

            # 标签（左侧，黑色）
            draw.text((margin + 15, current_y + pad_y), label_text, font=font_content, fill="#000000")

            # 数值（中间彩色加粗）
            label_bbox = draw.textbbox((0, 0), label_text, font=font_content)
            label_w = label_bbox[2] - label_bbox[0]
            value_bbox = draw.textbbox((0, 0), value_text, font=font_content)
            value_w = value_bbox[2] - value_bbox[0]
            # 居中位置
            total_mv_w = label_w + 20 + value_w + 20
            if delta_text:
                delta_bbox = draw.textbbox((0, 0), delta_text, font=font_content)
                total_mv_w += delta_bbox[2] - delta_bbox[0] + 20
            start_x = margin + 15
            value_x = start_x + label_w + 20
            draw.text((value_x, current_y + pad_y), value_text, font=font_content, fill=value_color)
            # 小字（右侧，黑色）
            if delta_text:
                delta_x = value_x + value_w + 20
                draw.text((delta_x, current_y + pad_y), delta_text, font=font_content, fill="#555555")

            current_y += rh

        else:
            # 普通内容行
            font = font_content
            text_color = "#000000"
            wrapped = wrap_text(row["text"], font, max_text_width, draw)
            line_h = row_height
            total_h = len(wrapped) * line_h
            rh = max(total_h, line_h)
            pad_y = 13  # 固定顶部内边距（稍大，往下调）
            draw.rectangle([margin, current_y, img_width - margin, current_y + rh], fill=row["bg_color"])
            for i, line in enumerate(wrapped):
                ly = current_y + i * line_h + pad_y
                draw.text((margin + 15, ly), line, font=font, fill=text_color)
            current_y += rh

    # 绘制底部备注
    footer_text = f"YOUDOO BOX 毛利测算模型 V6.7 | 生成时间：{now} | 售价模式：{price_mode} | 成本阶段：{use_channel_stage}"
    draw.rectangle([0, current_y, img_width, current_y + footer_height], fill="#F5F5F5")
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((img_width - footer_w)/2, current_y + 20), footer_text, font=font_footer, fill="#666666")

    # 转字节流
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# 生成按钮
if st.button("📥 生成方案信息图", type="primary", use_container_width=True):
    # 基础信息
    scheme_name = random.choice(SCHEME_NAME_LIST)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 生成图片
    img_bytes = create_scheme_image(scheme_name, now, price_mode, use_channel_stage)
    
    # 手机端提示
    st.success("✅ 方案信息图已生成！长按图片可以选择保存图片到手机相册")
    # 渲染原生图片（手机端长按可保存）
    st.image(img_bytes, use_column_width=True)
    # 额外增加一键下载按钮
    st.download_button(
        label="📥 一键下载PNG图片",
        data=img_bytes,
        file_name=f"YOUDOO售价方案_{scheme_name}版_{datetime.now().strftime('%Y%m%d')}.png",
        mime="image/png",
        use_container_width=True
    )
