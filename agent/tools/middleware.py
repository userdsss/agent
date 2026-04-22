from typing import Callable
from utils.prompt_loader import load_system_prompts, load_report_prompts
from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handler import logger

'''
{ToolCallRequest长这样
    # 1. 核心调用信息
    "tool_call": {
        "name": "get_weather",      # AI 想调用的工具名字
        "args": {"city": "深圳"},    # AI 传给工具的参数
        "id": "call_123abcd",       # 这一次调用的唯一 ID
        "type": "tool_call"
    },
    
    # 2. 运行时的上下文（非常重要！）
    "runtime": {
        "context": {                # 这是一个可以读写的字典
            "user_id": "1001",
            "report": False         # 你之前的代码就是在这里修改它
        },
        "config": { ... }           # 包含线程 ID、模型配置等
    }
}
'''
@wrap_tool_call #工具调用的拦截器
def monitor_tool(
        # 请求的数据封装
        request: ToolCallRequest,
        # 执行的函数本身
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:             # 工具执行的监控
    logger.info(f"[tool monitor]执行工具：{request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数：{request.tool_call['args']}")

    try:
        result = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")

#在 LangGraph 或复杂的 Agent 框架中，context（上下文）是一个在整个任务生命周期中都存在的 “共享字典”。
        if request.tool_call['name'] == "fill_context_for_report":
            request.runtime.context["report"] = True

        return result
    except Exception as e:
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        raise e
    
@before_model
def log_before_model(
        state: AgentState,          # 整个Agent智能体中的状态记录
        runtime: Runtime,           # 记录了整个执行过程中的上下文信息
):         # 在模型执行前输出日志
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息。")

    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}")

    return None


@dynamic_prompt                 # 每一次在生成提示词之前，调用此函数
def report_prompt_switch(request: ModelRequest):     # 动态切换提示词
    is_report = request.runtime.context.get("report", False)
    if is_report:               # 是报告生成场景，返回报告生成提示词内容
        return load_report_prompts()

    return load_system_prompts()
'''
{
AgentState长这样
    "messages": [
        HumanMessage(content="明天深圳天气如何？"),
        AIMessage(content="", tool_calls=[{"name": "get_weather", "args": {"city": "深圳"}}]),
        ToolMessage(content="晴天，26度", tool_call_id="call_abc")
    ],
    "user_id": "1001",
    "current_city": "深圳"
}

'''