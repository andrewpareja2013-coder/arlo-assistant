# =============================================================
# TIME_TOOL.PY
# Handles all time-related abilities: current time/date, greetings,
# alarms (set/list/cancel), and time-until calculations.
# Time format (12-hour vs 24-hour) is a per-account setting.
# Alarms are stored on the live backend under the account code.
# =============================================================

from datetime import datetime, timedelta
import requests
import config
import security
from tools.registry import register


def _uses_military_time():
    return security.get_setting("military_time", False)


def _match_alarm(memory, description):
    """Finds an alarm matching by description text OR by parsing the input as a time."""
    search = description.lower().strip()

    for a in memory.alarms:
        if not a["fired"] and a["description"].lower() != "n/a" and search in a["description"].lower():
            return a

    has_ampm = "am" in search or "pm" in search

    for fmt in ("%I:%M %p", "%I %p", "%I:%M%p", "%I%p", "%I:%M", "%I"):
        try:
            parsed_time = datetime.strptime(search.upper(), fmt).time()
            matches = [
                a for a in memory.alarms
                if not a["fired"] and a["time"].hour % 12 == parsed_time.hour % 12 and a["time"].minute == parsed_time.minute
            ]
            if not has_ampm and len(matches) > 1:
                return "AMBIGUOUS"
            if matches:
                return matches[0]
        except ValueError:
            continue

    return None


def get_time():
    now = datetime.now()
    return now.strftime("%H:%M") if _uses_military_time() else now.strftime("%I:%M %p")


def get_date():
    return datetime.now().strftime("%B %d, %Y")


def get_greeting_word():
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"


def set_alarm(memory, minutes_from_now=None, seconds_from_now=None, clock_time=None, description=None):
    if description is None:
        description = "N/A"

    now = datetime.now()

    if seconds_from_now is not None:
        fire_time = now + timedelta(seconds=seconds_from_now)
    elif minutes_from_now is not None:
        fire_time = now + timedelta(minutes=minutes_from_now)
    elif clock_time is not None:
        if "am" not in clock_time.lower() and "pm" not in clock_time.lower():
            return f"Did you mean {clock_time} AM or {clock_time} PM, sir?"
        fire_time = datetime.strptime(clock_time.upper(), "%I:%M %p")
        fire_time = fire_time.replace(year=now.year, month=now.month, day=now.day)
        if fire_time < now:
            fire_time += timedelta(days=1)
    else:
        return "I need a duration or a specific time to set an alarm, sir."

    response = requests.post(
        f"{config.API_BASE}/save-alarm",
        json={"account_id": memory.account_id, "fire_time": fire_time.isoformat(), "description": description},
        timeout=10,
    )
    new_id = response.json().get("id")
    memory.alarms.append({"id": new_id, "time": fire_time, "description": description, "fired": False})

    display = fire_time.strftime("%H:%M:%S") if _uses_military_time() else fire_time.strftime("%I:%M:%S %p")
    return f"Alarm set for {display}, sir."


def list_alarms(memory):
    active = [a for a in memory.alarms if not a["fired"]]
    if not active:
        return "You have no active alarms, sir."

    military = _uses_military_time()
    lines = []
    for a in active:
        display = a["time"].strftime("%H:%M") if military else a["time"].strftime("%I:%M %p")
        lines.append(f"{display} -- {a['description']}")
    return "Active alarms:\n" + "\n".join(lines)


def time_left_on_alarm(memory, description):
    a = _match_alarm(memory, description)
    if a == "AMBIGUOUS":
        return f"You have multiple alarms around '{description}', sir -- could you specify AM or PM?"
    if not a:
        return f"I couldn't find an active alarm matching '{description}', sir."

    now = datetime.now()
    diff = a["time"] - now
    total_seconds = int(diff.total_seconds())
    if total_seconds <= 0:
        return "That alarm should be going off right now, sir."

    if total_seconds < 3600:
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes} minutes and {seconds} seconds remain on that alarm, sir."
    else:
        rounded_minutes = round(total_seconds / 60)
        hours, minutes = divmod(rounded_minutes, 60)
        return f"{hours} hours and {minutes} minutes remain on that alarm, sir."


def cancel_alarm(memory, description):
    a = _match_alarm(memory, description)
    if a == "AMBIGUOUS":
        return f"You have multiple alarms around '{description}', sir -- could you specify AM or PM?"
    if not a:
        return f"I couldn't find an active alarm matching '{description}', sir."

    requests.post(f"{config.API_BASE}/delete-alarm", json={"id": a["id"]}, timeout=10)
    memory.alarms.remove(a)
    return f"Cancelled the alarm for {a['time'].strftime('%I:%M %p')}, sir."


def time_until(clock_time):
    if "am" not in clock_time.lower() and "pm" not in clock_time.lower():
        return f"Did you mean {clock_time} AM or {clock_time} PM, sir?"

    now = datetime.now()
    target = datetime.strptime(clock_time.upper(), "%I:%M %p")
    target = target.replace(year=now.year, month=now.month, day=now.day)
    if target < now:
        target += timedelta(days=1)

    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} hours and {minutes} minutes until {clock_time}, sir."


register(
    name="get_time",
    description="Get the current time. Use ONLY when the user explicitly asks what time it is.",
    parameters={"type": "object", "properties": {}},
    function=get_time,
    safe_to_test=True,
)

register(
    name="set_alarm",
    description=(
        "Set an alarm. Use seconds_from_now for short durations in seconds, "
        "minutes_from_now for durations in minutes, or clock_time for a specific "
        "time like '9:00 PM'. Only provide ONE of the three. NEVER ask the user "
        "for a description -- if none is given, proceed without one."
    ),
    parameters={
        "type": "object",
        "properties": {
            "seconds_from_now": {"type": "integer", "description": "Seconds from now to fire the alarm."},
            "minutes_from_now": {"type": "integer", "description": "Minutes from now to fire the alarm."},
            "clock_time": {"type": "string", "description": "A specific time like '3:00 PM'."},
            "description": {"type": "string", "description": "What the alarm is for. Optional."},
        },
        "required": [],
    },
    function=set_alarm,
    needs_memory=True,
)

register(
    name="time_left_on_alarm",
    description="Report how much time remains until a specific alarm fires.",
    parameters={
        "type": "object",
        "properties": {"description": {"type": "string", "description": "Text identifying which alarm."}},
        "required": ["description"],
    },
    function=time_left_on_alarm,
    needs_memory=True,
)

register(
    name="list_alarms",
    description="List all currently active alarms.",
    parameters={"type": "object", "properties": {}},
    function=list_alarms,
    needs_memory=True,
    safe_to_test=True,
)

register(
    name="cancel_alarm",
    description="Cancel an active alarm by description or time.",
    parameters={
        "type": "object",
        "properties": {"description": {"type": "string", "description": "Which alarm to cancel."}},
        "required": ["description"],
    },
    function=cancel_alarm,
    needs_memory=True,
)

register(
    name="time_until",
    description="Calculate how much time remains until a specific clock time.",
    parameters={
        "type": "object",
        "properties": {"clock_time": {"type": "string", "description": "The target time, e.g. '5:00 PM'."}},
        "required": ["clock_time"],
    },
    function=time_until,
)

register(
    name="get_date",
    description="Get today's date.",
    parameters={"type": "object", "properties": {}},
    function=get_date,
    safe_to_test=True,
)

register(
    name="get_greeting_word",
    description="Get whether it's currently morning, afternoon, or evening.",
    parameters={"type": "object", "properties": {}},
    function=get_greeting_word,
    safe_to_test=True,
)