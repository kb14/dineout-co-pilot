from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from src.prompts import SQL_AGENT_SYSTEM_PROMPT
from langgraph.prebuilt import create_react_agent

# Initialize database connection
DB = SQLDatabase.from_uri("sqlite:///db/dineout.db")

class AnalystAgent:
    def __init__(self, llm):
        self.llm = llm
        self.tools = SQLDatabaseToolkit(db=DB, llm=self.llm).get_tools()

    def run_analysis(self, query):
        agent_executor = create_react_agent(self.llm, self.tools, prompt=SQL_AGENT_SYSTEM_PROMPT)

        response_messages = agent_executor.invoke({"messages": [{"role": "user", "content": query}]})['messages']
        return response_messages[-1].content

