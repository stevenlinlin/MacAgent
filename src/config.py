import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash")
    #MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", "axterminator")
    #MCP_SERVER_ARGS = os.getenv("MCP_SERVER_ARGS", "mcp").split()
    BAIDU_APP_ID = os.getenv("BAIDU_APP_ID")
    BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
    BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")
    MORNING_CONTACT = os.getenv("MORNING_CONTACT", "little sun")
    MORNING_CITY = os.getenv("MORNING_CITY", "北京")
    SKILLS_DIR = os.getenv("SKILLS_DIR", "./skills")
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))