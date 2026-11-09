from langchain.agents.middleware import before_model, wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from typing import Callable
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from utils.logger_handler import logger 
from langchain.agents import AgentState
from langgraph.runtime import Runtime

@wrap_tool_call
def monitor_tool(
    request:ToolCallRequest,    #请求的数据封装（函数的入参）
    handler:Callable[[ToolCallRequest],ToolMessage | Command]     #执行的函数本身
    )->ToolMessage | Command:
    '''工具执行的监控'''
    logger.info(f"[monitor_tool]执行工具：{request.tool_call['name']}")
    logger.info(f"[monitor_tool]传入参数：{request.tool_call['args']}")
    try:
        result=handler(request)
        logger.info(f"[monitor_tool]工具{request.tool_call['name']}调用成功")

        return result
    except Exception as e:
        logger.error(f"[monitor_tool]工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        raise e

@before_model
def log_before_model(   
        state:AgentState,   #整个Agent智能体的状态记录
        runtime:Runtime     #记录了整个执行过程的上下文信息
):
    '''在模型执行前输出日志'''
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息")
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].text.strip()}")
    return None
