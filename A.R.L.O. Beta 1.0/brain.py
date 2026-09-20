# =============================================================
# BRAIN.PY
# The only file that talks to the AI model. The AI itself now runs
# on Cloudflare Workers AI (server-side), not locally via Ollama --
# this file just sends requests to our own /chat API endpoint.
# =============================================================

import json
import requests
import config
import security
from tools.registry import TOOLS
from tools.time_tool import get_greeting_word, get_date
from auto_register import load_all_tools
from error_codes import report_error

load_all_tools()


def build_system_prompt(memory):
    greeting_word = get_greeting_word()
    today = get_date()
    long_term = (
        f" What you remember about the user from past sessions: {memory.long_term_summary}"
        if memory.long_term_summary else ""
    )
    return (
        config.SYSTEM_PERSONALITY
        + f" It is currently the {greeting_word}, so greet the user accordingly if greeting them."
        + f" Today's real date is {today}. Use this to correctly judge whether events are in the past or future."
        + long_term
                + " CRITICAL: When reporting a time (from get_time, alarms, etc.), you MUST state it EXACTLY as given by the tool, character for character. NEVER convert between 12-hour and 24-hour format, NEVER add or remove AM/PM, NEVER rephrase it descriptively. Example: if the tool returns '08:39 PM', your answer must contain the literal text '08:39 PM' -- not '20:39', not '8:39pm', not any variation."
        + " CRITICAL: When searching for 'the most recent' or 'the last' occurrence of an annual/recurring event (like a Super Bowl, election, etc.), you MUST include the current year or a range of recent years in your search query, since generic searches return historical/evergreen pages, not the newest result. Cross-check the date mentioned in results against today's real date before answering."
        + " CRITICAL: When reporting a time (from get_time, alarms, etc.), state it EXACTLY as given by the tool -- never convert it to a different format or phrase it descriptively (like 'quarter past' or 'eight minutes before'). If the tool says '20:55', say '20:55', not a rephrased version."
        + " IMPORTANT: For any question involving current events, recent scores, prices, news, or "
          "anything that changes over time, you MUST use the web_search tool rather than answering "
          "from memory, since your own knowledge may be outdated or wrong."
        + " When using web_search results, ONLY state facts that are explicitly present in the "
          "search results. If the results don't clearly answer the question, say so honestly."
        + " When answering from web_search results, synthesize into a natural summary in your own "
          "words. Do not list out multiple website names or links as bullet points."
        + " CRITICAL: Alarm requests (set_alarm, list_alarms, cancel_alarm, time_left_on_alarm) MUST "
          "result in an actual tool call every single time, with no exceptions. Saying you've set an "
          "alarm without calling the tool is a serious failure -- never skip or simulate it."
        + " CRITICAL: If the user gives a clock_time for an alarm without specifying AM or PM, you "
          "MUST call set_alarm anyway and let the tool itself ask for clarification -- never guess "
          "AM/PM yourself, and never skip calling the tool."
    )


def get_tool_definitions():
    """Returns tool definitions in OpenAI-style function format for Workers AI."""
    definitions = []
    for name, info in TOOLS.items():
        definitions.append({
            "type": "function",
            "function": {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            },
        })
    return definitions


def run_tool(tool_name, tool_input, memory):
    if tool_name not in TOOLS:
        return "Unknown tool requested."

    tool_info = TOOLS[tool_name]

    if tool_info["requires_confirmation"]:
        memory.pending_action = {"tool_name": tool_name, "tool_input": tool_input}
        details = ", ".join(f"{k}: {v}" for k, v in tool_input.items()) if tool_input else "no additional details"
        return f"CONFIRMATION_NEEDED: About to run '{tool_name}' ({details}). Reply 'yes' to confirm, or anything else to cancel."

    function = tool_info["function"]

    try:
        if tool_info["needs_memory"]:
            result = function(memory, **tool_input) if tool_input else function(memory)
        elif tool_input:
            result = function(**tool_input)
        else:
            result = function()
    except Exception as e:
        report_error("E002", f"{tool_name}: {e}")
        return f"Error running {tool_name}: {e}"

    if isinstance(result, str) and result.startswith("NEEDS_APP_PATH:"):
        app_name = result.split(":", 1)[1]
        memory.pending_action = {"tool_name": "add_and_open_app", "tool_input": {"app_name": app_name}}
        return f"I don't have '{app_name}' set up yet, sir. What's its full file path or launch command?"

    if isinstance(result, str) and result.startswith("NEEDS_WEBSITE_URL:"):
        site_name = result.split(":", 1)[1]
        memory.pending_action = {"tool_name": "add_and_open_website", "tool_input": {"site_name": site_name}}
        return f"I don't have '{site_name}' set up yet, sir. What's its URL?"

    if tool_name in ["open_app", "close_app"]:
        memory.add_action(f"{tool_name}: {tool_input}")

    if config.TEST_MODE and security.can_see_debug():
        print(f"[DEBUG] {tool_name} called with {tool_input} -> result: {result}")

    return result


def _call_ai(messages, tools=None):
    """Sends a chat request to the live Cloudflare AI backend. Returns (message, neurons_used)."""
    payload = {"messages": messages}
    if tools:
        payload["tools"] = tools

    response = requests.post(f"{config.API_BASE}/chat", json=payload, timeout=30)
    data = response.json()
    if not data.get("success"):
        raise RuntimeError(data.get("error", "Unknown AI error"))
    message = data["response"]["choices"][0]["message"]
    usage = data["response"].get("usage") or {}
    neurons = usage.get("neurons", 1)
    return message, neurons


def get_reply(user_message, memory):
    username = security.get_current_username()
    usage_check = requests.get(f"{config.API_BASE}/check-usage", params={"username": username}, timeout=10).json()

    if not usage_check.get("allowed", True):
        return "I'm sorry sir, you've reached your daily usage limit. Please try again tomorrow."

    memory.add_message("user", user_message)
    total_usage = 0

    try:
        message, used = _call_ai(
            [{"role": "system", "content": build_system_prompt(memory)}] + memory.conversation,
            tools=get_tool_definitions(),
        )
        total_usage += used
    except Exception as e:
        report_error("E001", str(e))
        return "I'm sorry sir, I'm having trouble reaching my AI model right now. Please try again."

    tool_calls = message.get("tool_calls")

    if tool_calls:
        memory.conversation.append({"role": "assistant", "content": message.get("content") or "", "tool_calls": tool_calls})

        tool_result = None
        for call in tool_calls:
            tool_name = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            tool_input = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            tool_result = run_tool(tool_name, tool_input, memory)

            memory.conversation.append({
                "role": "tool",
                "content": f"RESULT for {tool_name}:\n{tool_result}\n\nInstruction: Base your answer ONLY on the information above."
            })

        try:
            followup, used = _call_ai([{"role": "system", "content": build_system_prompt(memory)}] + memory.conversation)
            total_usage += used
            reply_text = followup.get("content") or f"Done, sir: {tool_result}"
        except Exception as e:
            report_error("E001", str(e))
            reply_text = "I'm sorry sir, I completed the action but had trouble forming a response."
    else:
        reply_text = message.get("content", "")

    memory.add_message("assistant", reply_text)

    requests.post(f"{config.API_BASE}/add-usage", json={"username": username, "amount": total_usage}, timeout=10)

    return reply_text

def update_long_term_memory(memory):
    if len(memory.conversation) < 4:
        return

    transcript = "\n".join(
        f"{m['role']}: {m['content']}" for m in memory.conversation if isinstance(m.get("content"), str)
    )
    prompt = (
        "Summarize what's worth remembering about the user long-term from this conversation: "
        "their name, preferences, ongoing projects, and routines. "
        "Do NOT include sensitive info like SSN, home address, phone number, IP address, passwords, "
        "or financial details -- that belongs only in the password bank, never general memory. "
        f"Existing memory: {memory.long_term_summary}\n\nNew conversation:\n{transcript}"
    )
    try:
        message, used = _call_ai([{"role": "user", "content": prompt}])
        username = security.get_current_username()
        requests.post(f"{config.API_BASE}/add-usage", json={"username": username, "amount": used}, timeout=10)
    except Exception as e:
        report_error("E001", str(e))
        return
    memory.save_summary(message.get("content", ""))