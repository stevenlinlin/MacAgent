import streamlit as st
from st_audiorec import st_audiorec  # 使用已安装且可用的组件
from src.agent import build_agent
from src.voice_input_baidu import listen_once_from_file
import uuid
import tempfile
import os
from langchain_core.messages import HumanMessage
from src.skill_loader import discover_skills
import platform

if platform.system() != 'Darwin':
    st.info("ℹ️ 当前运行在云端演示环境，部分 macOS 本地操作（如打开微信、调节音量）将无法执行。但你可以体验对话和天气查询功能。")

# 页面配置
st.set_page_config(page_title="MacAgent 智能助手", layout="wide")
st.title("🤖 MacAgent 智能助手")
st.caption("macOS 自动化 · 语音/文本控制 · 多会话")

# 初始化会话状态
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.agent = build_agent()

# 侧边栏
with st.sidebar:
    st.header("🗂️ 会话")
    st.caption(f"当前会话: {st.session_state.thread_id[:8]}")
    if st.button("➕ 新建会话"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.header("📄 技能列表")
    skills = discover_skills()
    if skills:
        for s in skills:
            st.write(f"- {s['name']}: {s['description']}")
    else:
        st.write("暂无技能")

# 聊天界面
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 输入区：文本输入 + 语音按钮（带提示）
st.markdown("**🎤 点击 Start Recording，说话至少 3 秒，然后点击 Stop**")

col1, col2 = st.columns([5, 1])
with col1:
    prompt = st.chat_input("输入指令（如：打开微信、早上好）")
with col2:
    audio_bytes = st_audiorec()  # 返回 WAV 数据的字节

# 处理录音结果
if audio_bytes is not None:
    # 检查录音数据长度（正常录音应 > 2000 字节）
    if len(audio_bytes) < 2000:
        st.warning("⏳ 录音太短，请确保说话至少 3 秒再停止")
    else:
        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # 调用百度语音识别
        recognized_text = listen_once_from_file(tmp_path)
        
        # 显示识别结果
        if recognized_text and "错误" not in recognized_text and "失败" not in recognized_text:
            prompt = recognized_text
            st.success(f"✅ 语音识别: {recognized_text}")
        else:
            st.warning(f"❌ 识别出错: {recognized_text}")
        
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass

# 处理用户输入（文本或语音识别结果）
if prompt:
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 调用 Agent
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                result = st.session_state.agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=config
                )
                reply = result["messages"][-1].content
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.write(reply)
            except Exception as e:
                st.error(f"❌ 错误: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"错误: {e}"})