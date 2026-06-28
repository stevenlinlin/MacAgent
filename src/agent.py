import sys
import asyncio
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Annotated, List, Literal, TypedDict
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from src.config import Config
from src.skill_loader import discover_skills, load_skill_body
from src.mcp_official_client import MCPOfficialClient
#from src.voice_input import listen_for_command  # 直接导入函数
try:
    from src.voice_service import listen_for_command
except (ImportError, OSError):
    # 在无音频设备的服务器上，禁用语音输入
    def listen_for_command(timeout=5):
        return ""
    print("⚠️ 语音输入不可用（缺少音频设备或依赖），已禁用")


# ---------- 全局 MCP 客户端（单例） ----------
_mcp_client = None

def get_mcp_client():
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPOfficialClient()
    return _mcp_client

# ---------- 状态定义 ----------
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    selected_skill: str
    skill_params: dict
    skill_result: str
    step: int
    next_nodes: List[str]

# ---------- 初始化 LLM ----------
llm = ChatZhipuAI(
    api_key=Config.ZHIPUAI_API_KEY,
    model=Config.LLM_MODEL,
    temperature=0.1
)

# ---------- 早晨启动流程函数 ----------
def _run_morning_routine(mcp_client, contact: str = Config.MORNING_CONTACT, city: str = Config.MORNING_CITY) -> str:
    results = []
    try:
        # 1. 打开微信（捕获失败）
        try:
            success = asyncio.run(mcp_client.launch_app("WeChat"))
            results.append(f"微信启动: {'✅ 成功' if success else '❌ 失败'}")
            if not success:
                # 如果打开失败，提示用户当前环境不支持，但继续执行后续步骤？
                # 或者直接返回提示，让用户知道这是云环境限制
                return "⚠️ 当前部署环境为云端演示版，无法控制本地 macOS 应用。\n如需完整体验，请在 macOS 本地运行。"
        except Exception as e:
            return f"⚠️ 云端环境无法启动本地应用（{e}）。如需完整体验，请在 macOS 本地运行。"

        # 2. 查询天气（可以继续，因为天气 API 是联网的）
        weather_info = "未知"
        try:
            resp = requests.get(f"https://wttr.in/{city}?format=%C+%t", timeout=5)
            if resp.status_code == 200:
                weather_info = resp.text.strip()
            else:
                weather_info = "天气API不可用"
        except Exception as e:
            weather_info = f"天气查询失败: {str(e)}"

        # 3. 生成消息（即使微信没打开，也可以显示天气信息）
        if "sun" in weather_info.lower() or "晴" in weather_info:
            msg = f"早上好！今天天气不错（{weather_info}），建议出门走走。"
        else:
            msg = f"早上好！今天天气一般（{weather_info}），注意穿衣保暖。"

        # 4. 尝试发送微信消息（也会失败，但我们可以提示）
        try:
            success = asyncio.run(mcp_client.send_wechat_message(contact, msg))
            results.append(f"发送消息给 {contact}: {'✅ 成功' if success else '❌ 失败'}")
        except Exception as e:
            results.append(f"发送消息给 {contact}: ❌ 失败（云端环境无法发送微信）")

        # 5. 调节音量（同样失败，但提示）
        try:
            success = asyncio.run(mcp_client.set_volume(30))
            results.append(f"音量调节至30%: {'✅ 成功' if success else '❌ 失败'}")
        except Exception as e:
            results.append(f"音量调节至30%: ❌ 失败（云端环境无法调节音量）")

        # 最后返回汇总信息，包括天气信息，让用户知道流程走完了
        return f"🌅 早上好！\n{msg}\n\n执行摘要：\n" + "\n".join(results)
    except Exception as e:
        return f"❌ 早晨启动流程异常: {str(e)}"

# ---------- 节点函数 ----------
def router_node(state: AgentState):
    user_input = state["messages"][-1].content
    skills = discover_skills(Config.SKILLS_DIR)

    if not skills:
        return {
            "user_query": user_input,
            "next_nodes": [],
            "messages": [AIMessage(content="当前没有可用的 Skills，请先添加。")]
        }

    skill_desc = "\n".join([f"- {s['name']}: {s['description']}" for s in skills])

    prompt = f"""你是 macOS 自动化助手。根据用户需求，选择最合适的技能，并**仅返回 JSON 格式**，不要包含任何其他文字。

## 可用技能及其参数格式：
{skill_desc}

## 各技能的参数说明：
- **open_wechat**: 无需参数，parameters 为空对象 {{}}
- **open_safari**: 无需参数，parameters 为空对象 {{}}
- **control_volume**: 需要 action（up/down/mute/set）和 value（仅 set 时需要，0-100）
- **send_wechat_message**: 需要 contact（联系人）和 message（消息内容）
- **morning_routine**: 需要 contact（接收消息的联系人，可选，默认"little sun"）和 city（查询天气的城市，可选，默认"北京"）

## 返回格式：
{{
    "skill": "技能名称",
    "parameters": {{
        // 根据技能填充对应字段
    }}
}}

## 示例：
用户: "音量调到50%"
返回: {{"skill": "control_volume", "parameters": {{"action": "set", "value": 50}}}}

用户: "调高音量"
返回: {{"skill": "control_volume", "parameters": {{"action": "up"}}}}

用户: "给张三发消息明天开会"
返回: {{"skill": "send_wechat_message", "parameters": {{"contact": "张三", "message": "明天开会"}}}}

用户: "早上好"
返回: {{"skill": "morning_routine", "parameters": {{"contact": "little sun", "city": "北京"}}}}

用户: "打开微信"
返回: {{"skill": "open_wechat", "parameters": {{}}}}

用户: "启动Safari"
返回: {{"skill": "open_safari", "parameters": {{}}}}

如果不需要任何技能，返回 {{"skill": "none", "parameters": {{}}}}。

用户需求：{user_input}

输出:
"""
    response = llm.invoke([{"role": "user", "content": prompt}])
    raw_content = response.content.strip()

    # 移除可能存在的 Markdown 代码块标记
    if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
    elif raw_content.startswith("```"):
        raw_content = raw_content[3:]
    if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
    raw_content = raw_content.strip()

    try:
        import json
        decision = json.loads(raw_content)
        skill_name = decision.get("skill", "none")
        params = decision.get("parameters", {})
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 解析失败: {e}, 原始响应: {raw_content}")
        skill_name = "none"
        params = {}
    except Exception as e:
        print(f"⚠️ 未知错误: {e}")
        skill_name = "none"
        params = {}

    valid_skills = [s["name"] for s in skills]
    if skill_name in valid_skills:
        return {
            "user_query": user_input,
            "selected_skill": skill_name,
            "skill_params": params,
            "next_nodes": ["execute_skill"],
            "messages": [AIMessage(content=f"将执行技能: {skill_name}")]
        }
    else:
        return {
            "user_query": user_input,
            "selected_skill": "",
            "skill_params": {},
            "next_nodes": [],
            "messages": [AIMessage(content="未找到匹配的技能，请尝试其他描述。")]
        }

def execute_skill_node(state: AgentState):
    skill_name = state.get("selected_skill", "")
    skill_params = state.get("skill_params", {})
    user_query = state.get("user_query", "")

    if not skill_name:
        return {
            "skill_result": "未选择任何技能",
            "messages": [AIMessage(content="请指定要执行的技能。")]
        }

    result = ""
    mcp_client = get_mcp_client()

    # ---------- 打开应用类技能 ----------
    if skill_name in ["open_wechat", "open_safari"]:
        try:
            app_name = "WeChat" if skill_name == "open_wechat" else "Safari"
            success = asyncio.run(mcp_client.launch_app(app_name))
            if success:
                result = f"✅ {app_name} 已成功打开"
            else:
                result = f"❌ {app_name} 启动失败，可能是权限不足或应用未安装。"
        except Exception as e:
            result = f"❌ 打开应用时发生异常: {e}"

    # ---------- 音量控制类技能 ----------
    elif skill_name == "control_volume":
        action = skill_params.get("action")
        if not action:
            result = "❌ 缺少音量操作类型（up/down/mute/set）"
        else:
            value = skill_params.get("value")
            try:
                if action == "up":
                    result_dict = asyncio.run(mcp_client.volume_up())
                elif action == "down":
                    result_dict = asyncio.run(mcp_client.volume_down())
                elif action == "mute":
                    result_dict = asyncio.run(mcp_client.mute_volume())
                elif action == "set" and value is not None:
                    result_dict = asyncio.run(mcp_client.set_volume(value))
                else:
                    result_dict = {"success": False, "message": f"不支持的操作: {action}"}
                if result_dict:
                    result = f"✅ {result_dict} 已成功调节音量"
            except Exception as e:
                result = f"❌ 调节音量时发生异常: {e}"

    # ---------- 发送微信消息类技能 ----------
    elif skill_name == "send_wechat_message":
        contact = skill_params.get("contact")
        msg = skill_params.get("message")
        if not contact or not msg:
            result = "❌ 缺少联系人或消息内容"
        else:
            try:
                success = asyncio.run(mcp_client.send_wechat_message(contact, msg))
                result = f"✅ 消息已发送给 {contact}" if success else "❌ 发送失败"
            except Exception as e:
                result = f"❌ 发送消息时发生异常: {e}"

    # ---------- 早晨启动流程 ----------
    elif skill_name == "morning_routine":
        contact = skill_params.get("contact", Config.MORNING_CONTACT)
        city = skill_params.get("city", Config.MORNING_CITY)
        try:
            result = _run_morning_routine(mcp_client, contact, city)
        except Exception as e:
            result = f"❌ 早晨启动失败: {str(e)}"

    # ---------- 其他技能（fallback） ----------
    else:
        skill_body = load_skill_body(skill_name, Config.SKILLS_DIR)
        if not skill_body:
            return {
                "skill_result": f"技能 '{skill_name}' 未找到",
                "messages": [AIMessage(content=f"技能 '{skill_name}' 不存在。")]
            }
        prompt = f"你正在执行技能 '{skill_name}'。\n\n技能指令：{skill_body}\n\n用户需求：{user_query}\n请根据技能指令执行并给出结果。"
        response = llm.invoke([{"role": "user", "content": prompt}])
        result = response.content

    return {
        "skill_result": result,
        "messages": [AIMessage(content=result)],
        "step": state.get("step", 0) + 1
    }

def should_continue(state: AgentState) -> Literal["execute_skill", "__end__"]:
    if state.get("next_nodes", []) and state.get("step", 0) < Config.MAX_ITERATIONS:
        return "execute_skill"
    return "__end__"

# ---------- 构建 Agent 图（供 Web 和命令行使用） ----------
def build_agent():
    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("execute_skill", execute_skill_node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        should_continue,
        {"execute_skill": "execute_skill", "__end__": END}
    )
    builder.add_edge("execute_skill", END)
    return builder.compile(checkpointer=MemorySaver())

# ---------- 主程序 ----------
def main():
    print("=" * 60)
    print("🤖 MacAgent — macOS 自动化智能体（MCP 模式）")
    print("=" * 60)
    print("示例指令：打开微信、启动 Safari、早上好")
    print("输入 'exit' 退出\n")

    agent = build_agent()
    config = {"configurable": {"thread_id": "macagent_session"}}

    use_voice = input("是否启用语音输入？(y/n): ").lower() == 'y'

    while True:
        if use_voice:
            user_input = listen_for_command()
            if not user_input:
                print("未检测到语音，请输入文本：")
                user_input = input("👤 你: ")
        else:
            user_input = input("\n👤 你: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        try:
            result = agent.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config
            )
            print(f"\n🤖 Agent: {result['messages'][-1].content}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()