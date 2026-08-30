import json

from app.reasoning.action import Action
from app.reasoning.thought import Thought


def safe_load(raw):
    try:
        value = json.loads(str(raw or "").strip())
        return value, None
    except (TypeError, json.JSONDecodeError) as error:
        return None, str(error)


def parse_action(payload):
    if not isinstance(payload, dict):
        raise ValueError("Action must be a JSON object")
    tool = payload.get("tool")
    action = payload.get("action")
    arguments = payload.get("arguments", payload.get("input", {}))
    if not isinstance(tool, str) or not tool.strip() or not isinstance(action, str) or not action.strip():
        raise ValueError("Action requires tool and action strings")
    if not isinstance(arguments, dict):
        argument_key = {"file": "path", "search": "query", "terminal": "command"}.get(tool, "code")
        arguments = {argument_key: arguments}
    return Action(tool=tool.strip(), action=action.strip(), arguments=arguments)


def parse_thought(raw, step=1):
    payload, error = safe_load(raw)
    if error:
        raise ValueError("Response is not valid JSON") from None
    if not isinstance(payload, dict):
        raise ValueError("Response must be a JSON object")
    action = parse_action(payload)
    finished = payload.get("finished", payload.get("finish", False))
    if not isinstance(finished, bool):
        raise ValueError("Finished must be boolean")
    confidence = payload.get("confidence", 1.0)
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        confidence = 1.0
    return Thought(
        thought=payload.get("thought", payload.get("text", "")),
        tool=action.tool,
        action=action.action,
        arguments=action.arguments,
        finished=finished,
        step=step,
        confidence=float(confidence),
        reasoning=payload.get("reasoning", payload.get("reason", "")),
    )


def fallback(step=1):
    return Thought("No valid thought was produced.", "", "", step=step)