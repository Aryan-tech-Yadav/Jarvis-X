import json
import re
from typing import Optional

from app.ai.ai_manager import AIManager
from app.utils.json_utils import clean_json
from app.core.logger import Logger
from app.prompts.planner_prompt import PLANNER_PROMPT


class ProjectPlanner:
     
     
    def __init__(self):
        self.ai = AIManager()
         
    def plan(self, prompt, project_name=None, folders=None):
        extra = ""
        if project_name:
            extra += f"Project name must be: {project_name}\n"
        if folders:
            extra += "Required folders (must create all of these):\n"
            for folder in folders:
                extra += f"  - {folder}\n"
            extra += "\n"
        
        full_prompt = extra + PLANNER_PROMPT.format(user_prompt=prompt)

        response = self.ai.ask(full_prompt)
        
        Logger.info("RAW_RESPONSE")
        Logger.info(response)

        
        response = clean_json(response)
        
        Logger.info("After Clean:")
        Logger.info(response)
        

        try:
            return json.loads(response)

        except json.JSONDecodeError as error:
            Logger.error("INVALID JSON")
            Logger.error(response)
            
            # Try to extract JSON with regex as fallback
            extracted = self._extract_json(response)
            if extracted:
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    pass
            
            Logger.error(f"Failed to parse project design JSON: {error}")
            return None

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extract the first JSON object from text using brace matching."""
        if not text or "{" not in text:
            return None
        
        start = text.find("{")
        if start == -1:
            return None
        
        # Try to find matching closing brace
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == "\\" and in_string:
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if in_string:
                continue
                
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        
        return None