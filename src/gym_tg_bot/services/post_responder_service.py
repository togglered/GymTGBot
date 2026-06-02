import structlog

from gym_tg_bot.chat import ChatMessage, ToolCall, ToolResult
from gym_tg_bot.llm import LLMClient
from gym_tg_bot.memory import ThreadMemory
from gym_tg_bot.tools.base import Tool, ToolContext


class PostResponderService:
    def __init__(self, llm: LLMClient, memory: ThreadMemory, tools: list[Tool]) -> None:
        self._llm = llm
        self._memory = memory
        self._tools_by_name = {t.definition["function"]["name"]: t for t in tools}  # type: ignore[index]
        self._tool_definitions = [t.definition for t in tools]

    async def respond(
        self,
        chat_id: int,
        thread_id: int,
        text: str,
        system_prompt: str,
    ) -> str:
        context = ToolContext(chat_id=chat_id)
        log = structlog.get_logger().bind(chat_id=chat_id, thread_id=thread_id)
        log.info(
            "respond start",
            text_preview=text[:80],
            available_tools=list(self._tools_by_name.keys()),
        )
        await self._memory.add(chat_id, thread_id, ChatMessage("user", text))
        messages: list[ChatMessage | ToolCall | ToolResult] = await self._memory.get(
            chat_id, thread_id
        )

        iteration = 0
        while True:
            iteration += 1
            log.info("llm call", iteration=iteration, messages_count=len(messages))
            result = await self._llm.chat_with_tools(
                system=system_prompt,
                messages=messages,
                tools=self._tool_definitions,
            )
            if isinstance(result, str):
                log.info(
                    "respond finish",
                    iteration=iteration,
                    answer_preview=result[:120],
                )
                await self._memory.add(chat_id, thread_id, ChatMessage("assistant", result))
                return result
            log.info(
                "llm requested tool calls",
                iteration=iteration,
                tool_calls=[{"name": tc.name, "arguments": tc.arguments} for tc in result],
            )
            for tool_call in result:
                messages.append(tool_call)
                output = await self._execute_tool(tool_call, context, log)
                messages.append(output)

    async def _execute_tool(
        self, tool_call: ToolCall, context: ToolContext, log: "structlog.stdlib.BoundLogger"
    ) -> ToolResult:
        handler = self._tools_by_name.get(tool_call.name)
        if handler is None:
            log.error("unknown tool requested", tool_name=tool_call.name)
            raise ValueError(f"Unknown tool: {tool_call.name}")
        log.info(
            "tool exec start",
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            arguments=tool_call.arguments,
        )
        try:
            content = await handler(tool_call.arguments, context)
        except Exception:
            log.exception(
                "tool exec failed",
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
            )
            raise
        log.info(
            "tool exec done",
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            result_preview=content[:200],
        )
        return ToolResult(tool_call_id=tool_call.id, content=content)
