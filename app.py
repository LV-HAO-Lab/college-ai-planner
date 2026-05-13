import pandas as pd
from datetime import datetime
from openai import OpenAI
import streamlit as st
import os

# -------------------------- 配置区 --------------------------
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# -------------------------- 校园美食分类（不分食堂，按类型推荐） --------------------------
food_recommend = {
    "主食": [
        "二楼食堂自选菜性价比高，菜品多、打饭快",
        "一楼食堂江湖麻辣烫/拌味道好",
        "一楼食堂椒太浪油麻鸡米饭,小菜面筋烤辣椒美味🤤",
        "二楼食堂港式滑蛋饭，吃了都说好",
        "三楼食堂瓦香鸡米饭，汁水特别足"
    ],
    "快餐": [
        "强推食堂一楼临榆炸鸡腿，解馋神器",
        "餐厅负一楼0090汉堡工厂，性价比首选",
        "食堂一楼塔斯汀.汉堡，月初直接冲"
    ],
    "饮品": [
        "食堂一楼幸运咖，二楼雪王，性价比之选",
        "校内还有库迪咖啡，琉璃净茶饮"
    ],
    "早餐": [
        "一楼食堂有包子，牛肉卷饼，掉渣饼等等早八严选",
        "也有花样饼母鸡汤，牛肉胡辣汤等悠闲早餐"
    ]
}

# 自习室、周末出行不变
campus_study = [
    "图书馆周一到周日：7：30 - 22：00（注：周四从中午12点开始闭馆）📖",
    "教三楼无上课需求的空教室都可以用来自习🧑‍🎓",
    "部分实验室也可以在参加社团后用来自习使用💻"
]
campus_travel = [
    "附近有正弘城，360商圈🏬",
    "学校出门500米是地铁站🚇，可以到达郑州绝大多数游玩地方",
    "河南省博物馆免费预约参观🏛️"
]


# -------------------------- 文件读写（按学号分文件） --------------------------
def get_student_csv_path(stu_id):
    return f"schedule_{stu_id}.csv"


def load_student_schedule(stu_id):
    path = get_student_csv_path(stu_id)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["课程名", "星期", "开始节数", "结束节数", "地点"])


def save_student_schedule(stu_id, df):
    path = get_student_csv_path(stu_id)
    df.to_csv(path, index=False)


# -------------------------- 功能函数 --------------------------
def generate_plan_by_weekday(weekday_idx, schedule_df):
    if schedule_df.empty:
        return None, "⚠️ 你还没有录入课表，请先去录入！"

    today_classes = schedule_df[schedule_df["星期"] == weekday_idx].copy()
    if today_classes.empty:
        return None, "✅ 这天没课！好好休息或复习~"

    today_classes["节次"] = today_classes.apply(
        lambda x: f"{x['开始节数']}-{x['结束节数']}节", axis=1
    )
    display_df = today_classes[["课程名", "节次", "地点"]].reset_index(drop=True)
    return display_df, None


# ===================== AI 三角色对话 =====================
def ai_chat(user_input, api_key, role):
    if role == "缓解情绪压力师":
        system_prompt = "你是一位温柔、耐心、温暖的情绪疏导师，专门安慰大学生，缓解压力、焦虑、emo、不开心，语气亲切治愈、像朋友一样陪伴开导。"
    elif role == "资料查找大师":
        system_prompt = "你是专业资料查找大师，回答简洁准确，帮大学生查学习资料、知识点、常识、课程信息、各类文字查询，直接给出清晰答案。"
    elif role == "解题大师":
        system_prompt = "你是专业解题大师，专门给大学生解答各科题目：数学、物理、英语、专业课等。一定要一步步详细拆解步骤，讲清思路、公式、知识点、易错点，通俗易懂。"

    try:
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用失败：{str(e)}"


# -------------------------- 页面美化 --------------------------
st.set_page_config(
    page_title="郑州轻工·大学生AI规划师",
    page_icon="🎓",
    layout="wide"
)

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

st.markdown('<div class="main-title">🎓 郑州轻工·大学生AI规划师</div>', unsafe_allow_html=True)
st.divider()

# ===================== 让用户输入自己的 API Key =====================
st.subheader("🔑 AI聊天配置")
api_key_input = st.text_input("请输入你的 DeepSeek API Key", type="password", placeholder="sk-xxxxxxxxxxxxxxxxxxxx")
st.caption("课表、美食推荐功能无需API Key，可直接使用")

st.divider()

# ===================== 学号登录模块（登录后自动隐藏） =====================
if "login_stu_id" not in st.session_state:
    st.session_state.login_stu_id = ""

# 未登录状态：只显示登录框
if not st.session_state.login_stu_id:
    st.subheader("👤 学号登录")
    stu_id_input = st.text_input("请输入你的学号登录", placeholder="例如：542513390124")

    if st.button("登录"):
        if stu_id_input.strip():
            st.session_state.login_stu_id = stu_id_input.strip()
            st.session_state.my_schedule = load_student_schedule(st.session_state.login_stu_id)
            st.success(f"✅ 学号 {st.session_state.login_stu_id} 登录成功！")
            st.rerun()  # 关键：登录后刷新页面，自动隐藏登录框
        else:
            st.warning("请输入学号！")
    st.stop()  # 没登录就停在这里，不显示后面的功能区

# 已登录状态：不再显示登录框，直接显示主功能
st.subheader(f"👋 欢迎你，学号 {st.session_state.login_stu_id}！")

# ===================== 手动录入自己的课表（按学号保存） =====================
st.subheader("📝 手动录入我的课表")
with st.expander("点击展开录入课表", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        course_name = st.text_input("课程名称")
        weekday = st.selectbox("星期", ["周一", "周二", "周三", "周四", "周五"])
        location = st.text_input("上课地点")
    with col2:
        start = st.number_input("开始节数", min_value=1, max_value=10, value=1)
        end = st.number_input("结束节数", min_value=1, max_value=10, value=2)

    week_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4}

    if st.button("✅ 添加这门课"):
        if course_name and location:
            new_row = {
                "课程名": course_name,
                "星期": week_map[weekday],
                "开始节数": start,
                "结束节数": end,
                "地点": location
            }
            st.session_state.my_schedule = pd.concat(
                [st.session_state.my_schedule, pd.DataFrame([new_row])],
                ignore_index=True
            )
            save_student_schedule(st.session_state.login_stu_id, st.session_state.my_schedule)
            st.success("添加成功！已自动保存到你的学号账号～")
        else:
            st.warning("课程名和地点不能为空！")

    if not st.session_state.my_schedule.empty:
        st.markdown("### 📋 我的已录入课表")
        st.dataframe(st.session_state.my_schedule, use_container_width=True, hide_index=True)

    if st.button("🗑️ 清空我的所有课表"):
        st.session_state.my_schedule = pd.DataFrame(columns=["课程名", "星期", "开始节数", "结束节数", "地点"])
        save_student_schedule(st.session_state.login_stu_id, st.session_state.my_schedule)
        st.success("已清空并保存！")

# ===================== 功能菜单 =====================
menu = st.radio(
    "选择功能模块",
    ["📅 课表查询", "🏫 校园生活推荐", "💬 AI智能助手"],
    horizontal=True
)

if menu == "📅 课表查询":
    st.subheader("📅 查看我的课程安排")
    week_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4}
    selected_day = st.selectbox("选择星期", list(week_map.keys()))
    idx = week_map[selected_day]

    df, empty_msg = generate_plan_by_weekday(idx, st.session_state.my_schedule)
    st.markdown(f"### 📌 {selected_day} 我的课程表")
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

elif menu == "🏫 校园生活推荐":
    st.subheader("🏫 校园智能推荐")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        type_choice = st.radio("选择推荐类型", ["食堂美食", "自习室", "周末出行"], horizontal=True)

        if type_choice == "食堂美食":
            food_type = st.selectbox("选择美食类型", list(food_recommend.keys()))
            st.markdown("### 🍽️ 美食推荐")
            for item in food_recommend[food_type]:
                st.write(f"- {item}")

        elif type_choice == "自习室":
            st.markdown("### 📚 自习室推荐")
            for item in campus_study:
                st.write(f"- {item}")

        elif type_choice == "周末出行":
            st.markdown("### 🎉 周末出行推荐")
            for item in campus_travel:
                st.write(f"- {item}")

        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "💬 AI智能助手":
    st.subheader("💬 AI 智能助手")
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        role = st.radio("选择AI助手类型", [
            "💖 缓解情绪压力师",
            "📚 资料查找大师",
            "🧠 解题大师"
        ], horizontal=True)

        real_role = role.replace("💖 ", "").replace("📚 ", "").replace("🧠 ", "")

        msg = st.text_input("请输入你想咨询/解答的内容~")

        if msg:
            if not api_key_input:
                st.warning("请先在顶部输入你的 DeepSeek API Key")
            else:
                with st.spinner("AI正在思考解答中..."):
                    reply = ai_chat(msg, api_key_input, real_role)
                    st.info(reply)

        st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("⚠️ 提示：本工具仅为学习辅助，所有安排请以学校通知为准")