import sys
from pathlib import Path

if __name__ == "__main__" and not __package__:
    # 直接运行脚本时，让 Python 能找到项目根目录下的模块。
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from agent.tools.agent_tools import OrderContext, get_order, list_my_orders, rag_summarize
from agent.tools.midddleware import log_before_model, monitor_tool
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts


class ReactAgent:
    def __init__(self, *, remember_history: bool = False):
        self.remember_history = remember_history
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[rag_summarize, get_order, list_my_orders],
            middleware=[monitor_tool, log_before_model],
            context_schema=OrderContext,
            checkpointer=InMemorySaver() if remember_history else None,
        )

    def execute_stream(self, query: str, *, user_id: str = ""):
        user_id = user_id.strip()
        config = None
        if self.remember_history:
            config = {"configurable": {"thread_id": f"order:{user_id}"}}

        input_dict = {"messages": [{"role": "user", "content": query}]}
        for chunk in self.agent.stream(
            input_dict,
            config=config,
            stream_mode="values",
            context=OrderContext(user_id=user_id),
        ):
            latest_message = chunk["messages"][-1]
            if isinstance(latest_message, AIMessage) and not latest_message.tool_calls:
                response = latest_message.text.strip()
                if response:
                    yield response + "\n"

if __name__ == "__main__":
    agent = ReactAgent(remember_history=True)
    default_user_id = "sophia_garcia_1101"
    try:
        user_id = input(f"模拟用户 ID（回车使用 {default_user_id}）：").strip() or default_user_id
        print("输入问题开始对话，输入 exit 或 退出 结束。")
        while True:
            query = input("\n你：").strip()
            if query.lower() in {"exit", "退出"}:
                break
            if not query:
                continue
            print("Agent：", end="", flush=True)
            for chunk in agent.execute_stream(query, user_id=user_id):
                print(chunk, end="", flush=True)
    except (EOFError, KeyboardInterrupt):
        print()
