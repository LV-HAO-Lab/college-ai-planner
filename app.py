import pandas as pd
from datetime import datetime
from openai import OpenAI
import streamlit as st

# -------------------------- 配置区 --------------------------
DEEPSEEK_API_KEY = "sk-d5f62f99288b41a580fe7cdaa4640c5b"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 校园数据
campus_data = {
    "食堂": ["一食堂三楼麻辣烫人少好吃", "二食堂二楼自选菜性价比高", "三食堂早餐丰富"],
    "自习室": ["图书馆3楼安静刷题", "教学楼B栋101空课多", "实训楼5楼机房人少"],
    "周末出行": ["附近公园散步", "大学城商业街逛街", "市博物馆免费放松"]
}


# 课表数据
def get_demo_schedule():
    data = {
        "课程名": [
            "高等数学A2", "高等数学A2", "大学英语视听说A2",
            "大学物理B", "大学体育2", "大学英语视听说A2", "实验",
            "线性代数与空间解析几何", "线性代数与空间解析几何", "高等数学A2",
            "大学物理B", "人工智能概论", "劳动教育"
        ],
        "星期": [0, 1, 1, 0, 0, 1, 1, 0, 2, 3, 3, 3, 4],
        "开始节数": [1, 1, 1, 3, 3, 3, 3, 5, 5, 5, 7, 9, 9],
        "结束节数": [2, 2, 2, 4, 4, 4, 4, 6, 6, 6, 8, 10, 10],
        "地点": [
            "教三楼201", "教三楼208", "教一楼203",
            "教三楼209", "操场", "教一楼301", "1004",
            "教三楼509", "教三楼509", "教三楼109",
            "教三楼301", "教三楼104", "待定"
        ]
    }
    return pd.DataFrame(data)


# -------------------------- 功能函数 --------------------------
def generate_plan_by_weekday(weekday_idx):
    df = get_demo_schedule()
    today_classes = df[df["星期"] == weekday_idx].copy()
    if today_classes.empty:
        return None, "🎉 这天没课！好好休息或复习~"
    # 整理表格格式
    today_classes["节次"] = today_classes.apply(
        lambda x: f"{x['开始节数']}-{x['结束节数']}节", axis=1
    )
    display_df = today_classes[["课程名", "节次", "地点"]].reset_index(drop=True)
    return display_df, None


def scene_recommend(user_input):
    user_input = user_input.lower()
    if any(w in user_input for w in ["食堂", "吃饭", "餐厅"]):
        return "🍚 食堂推荐：\n" + "\n".join([f"- {x}" for x in campus_data["食堂"]])
    elif any(w in user_input for w in ["自习室", "自习", "学习", "图书馆"]):
        return "📖 自习室推荐：\n" + "\n".join([f"- {x}" for x in campus_data["自习室"]])
    elif any(w in user_input for w in ["周末", "出行", "玩", "放松"]):
        return "🚶 周末推荐：\n" + "\n".join([f"- {x}" for x in campus_data["周末出行"]])
    else:
        return "💡 输入关键词：食堂 / 自习室 / 周末"


def emotion_support_chat(user_input):
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是温柔的大学生AI规划师，简短亲切、鼓励像朋友"},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=512
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 调用失败：{str(e)}"


# -------------------------- 美化界面 --------------------------
st.set_page_config(
    page_title="校享·大学生AI规划师",
    page_icon="📚",
    layout="wide"
)

# 标题与样式
st.markdown("""
<style>
.main-title {
    font-size: 2.2rem;
    font-weight: bold;
    color: #4F8BF9;
    text-align: center;
    margin-bottom: 1rem;
}
.card {
    background-color: #f0f2f6;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📚 校享·大学生AI规划师</div>', unsafe_allow_html=True)
st.divider()

# 功能选择
menu = st.radio(
    "选择功能模块",
    ["📅 课表查询", "🍚 校园生活推荐", "💬 AI情绪聊天"],
    horizontal=True
)

if menu == "📅 课表查询":
    st.subheader("🗓 查看任意一天的课程安排")
    week_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4}
    selected_day = st.selectbox("选择星期", list(week_map.keys()))
    idx = week_map[selected_day]

    df, empty_msg = generate_plan_by_weekday(idx)
    st.markdown(f"### 📅 {selected_day} 课程表")
    if df is not None:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "课程名": st.column_config.TextColumn("课程名称", width="medium"),
                "节次": st.column_config.TextColumn("节次", width="small"),
                "地点": st.column_config.TextColumn("上课地点", width="medium")
            }
        )
        st.success("💡 课后花30分钟整理笔记，效率更高哦！")
    else:
        st.info(empty_msg)

elif menu == "🍚 校园生活推荐":
    st.subheader("🔍 校园场景智能推荐")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        txt = st.text_input("输入需求关键词（例：食堂/自习室/周末）")
        if txt:
            st.text_area("推荐结果", scene_recommend(txt), height=180)
        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💬 AI情绪聊天":
    st.subheader("🤗 和AI聊聊学习与心情")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        msg = st.text_input("说点什么吧~")
        if msg:
            st.info(emotion_support_chat(msg))
        st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("💡 提示：本工具仅为学习辅助，所有安排请以学校通知为准")