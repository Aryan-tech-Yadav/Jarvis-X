import json
import re
from typing import Optional

from app.ai.ai_manager import AIManager
from app.utils.json_utils import clean_json
from app.core.logger import Logger
from app.prompts.planner_prompt import PLANNER_PROMPT


class ProjectPlanner:
     
     
    def __init__(self, use_reconnaissance=False, reconnaissance_adapter=None):
        self.ai = AIManager()
        self.use_reconnaissance = use_reconnaissance
        self.reconnaissance_adapter = reconnaissance_adapter
         
    def plan(self, prompt, project_name=None, folders=None):
        if self.use_reconnaissance:
            original_prompt = prompt
            try:
                from app.project.reconnaissance_adapter import ReconnaissanceAdapter

                adapter = self.reconnaissance_adapter or ReconnaissanceAdapter()
                prompt, _blueprint = adapter.prepare_prompt(prompt)
            except Exception as exc:
                prompt = original_prompt
                print(
                    f"[WARN] Reconnaissance failed; "
                    f"using original planner: {exc}"
                )

        extra = ""
        if project_name:
            extra += f"Project name must be: {project_name}\n"
        if folders:
            extra += "Required folders (must create all of these):\n"
            for folder in folders:
                extra += f"  - {folder}\n"
            extra += "\n"
        
        full_prompt = extra + PLANNER_PROMPT.format(user_prompt=prompt)

        response = (
            self.ai.ask(full_prompt, format="json")
            if self.use_reconnaissance
            else self.ai.ask(full_prompt)
        )
        
        Logger.info("RAW_RESPONSE")
        Logger.info(response)

        
        response = clean_json(response)
        
        Logger.info("After Clean:")
        Logger.info(response)
        

        try:
            result = json.loads(response)
            if self.use_reconnaissance:
                validation_error = self._validate_plan(
                    result,
                    require_tests=self._request_requires_tests(original_prompt),
                )
                if validation_error:
                    Logger.error(f"Invalid reconnaissance plan: {validation_error}")
                    return self._retry_reconnaissance_plan(
                        full_prompt, original_prompt, validation_error
                    )
            return result

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
            
            # Retry once only when reconnaissance mode is enabled.
            # Keep the existing planner behavior unchanged by default.
            if self.use_reconnaissance:
                retry_prompt = (
                    "Your previous response was not valid JSON. "
                    "Generate the complete project plan again. "
                    "Return ONLY one valid JSON object matching the "
                    "project planner schema. Ensure all brackets, "
                    "quotes, and commas are correct. Do not truncate "
                    "the response or include markdown.\n\n"
                    "Original planning request and required schema:\n"
                    + full_prompt
                )
                try:
                    Logger.info(
                        "Retrying planner once because JSON parsing failed."
                    )
                    retry_response = (
                        self.ai.ask(retry_prompt, format="json")
                        if self.use_reconnaissance
                        else self.ai.ask(retry_prompt)
                    )
                    retry_response = clean_json(retry_response)

                    try:
                        result = json.loads(retry_response)
                    except (json.JSONDecodeError, TypeError):
                        extracted = self._extract_json(retry_response)
                        result = json.loads(extracted) if extracted else None

                    if self.use_reconnaissance and result is not None:
                        validation_error = self._validate_plan(
                            result,
                            require_tests=self._request_requires_tests(original_prompt),
                        )
                        if validation_error is None:
                            Logger.info("Planner retry returned a valid plan.")
                            return result
                        Logger.error(
                            f"Planner retry plan validation failed: {validation_error}"
                        )
                    else:
                        Logger.error("Planner retry did not return a valid plan.")

                except Exception as retry_error:
                    Logger.error(f"Planner retry failed: {retry_error}")

            Logger.error(f"Failed to parse project design JSON: {error}")
            return None

    def _retry_reconnaissance_plan(
        self, full_prompt, original_prompt, validation_error
    ):
        """Retry once to correct an invalid reconnaissance plan."""
        retry_prompt = (
            "Correct your previous project plan and return ONLY valid JSON. "
            "Fix this validation error: " + validation_error + "\\n"
            "The files array may contain only actual files, never folders. "
            "Each file object must have only name and type. "
            "Allowed file types: python and txt.\\n\\n"
            "Original request and schema:\\n" + full_prompt
        )
        try:
            Logger.info("Retrying reconnaissance planner after validation failure.")
            response = clean_json(self.ai.ask(retry_prompt, format="json"))
            try:
                result = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                extracted = self._extract_json(response)
                result = json.loads(extracted) if extracted else None

            if result is None:
                Logger.error("Correction retry returned invalid JSON.")
                return None

            error = self._validate_plan(
                result,
                require_tests=self._request_requires_tests(original_prompt),
            )
            if error:
                Logger.error(f"Correction retry failed validation: {error}")
                return None

            Logger.info("Correction retry returned a valid plan.")
            return result
        except Exception as exc:
            Logger.error(f"Correction retry failed: {exc}")
            return None

    @staticmethod
    def _request_requires_tests(prompt):
        """Detect explicit requests for tests without forcing them on every project."""
        prompt = prompt.lower()
        return any(term in prompt for term in (
            "unit test", "unit tests", "pytest", "test coverage",
            "include tests", "include test files",
        ))

    @staticmethod
    def _validate_plan(result, require_tests=False):
        """Validate schema, paths, and explicitly requested test deliverables."""
        if not isinstance(result, dict):
            return "Plan must be a JSON object."

        if not {"project_name", "folders", "files"}.issubset(result):
            return "Missing required keys: project_name, folders, or files."

        if not isinstance(result["project_name"], str) or not result["project_name"].strip():
            return "project_name must be a non-empty string."

        folders = result["folders"]
        files = result["files"]

        if not isinstance(folders, list) or not all(
            isinstance(folder, str) and folder.strip() for folder in folders
        ):
            return "folders must be a list of non-empty strings."

        if not isinstance(files, list) or not files:
            return "files must be a non-empty list."

        seen_folders = set()
        for folder in folders:
            normalized = folder.replace("\\\\", "/").strip("/")
            if (
                not normalized
                or normalized.startswith("/")
                or any(part in {"", ".", ".."} for part in normalized.split("/"))
            ):
                return f"Unsafe folder path: {folder}"
            if normalized in seen_folders:
                return f"Duplicate folder path: {folder}"
            seen_folders.add(normalized)

        seen_files = set()
        for item in files:
            if not isinstance(item, dict):
                return "Each file entry must be an object."
            name = item.get("name")
            file_type = item.get("type")
            if not isinstance(name, str) or not name.strip():
                return "Each file must have a non-empty name."
            if file_type not in {"python", "txt"}:
                return f"Unsupported file type for {name}: {file_type}"

            normalized = name.replace("\\\\", "/")
            parts = normalized.split("/")
            if (
                normalized.startswith("/")
                or any(part in {"", ".", ".."} for part in parts)
            ):
                return f"Unsafe file path: {name}"
            if normalized in seen_files:
                return f"Duplicate file path: {name}"
            seen_files.add(normalized)

        # Reject paths that conflict with explicitly declared folders.
        file_paths = set(seen_files)
        for folder in seen_folders:
            if folder in file_paths:
                return f"Path is both a folder and a file: {folder}"
            if any(file_path.startswith(folder + "/") for file_path in file_paths):
                continue

        # Require files to live inside a declared folder when one matches
        # their intended location. Root-level files remain allowed.
        for file_path in file_paths:
            parent = file_path.rpartition("/")[0]
            if parent and parent not in seen_folders:
                return f"File parent folder is not declared: {file_path}"

        if require_tests and not any(
            name.endswith(".py")
            and (
                name.startswith("tests/")
                or name.startswith("test_")
                or "/test_" in name
                or name.endswith("_test.py")
                or name.endswith("_tests.py")
            )
            for name in seen_files
        ):
            return "Tests were requested, but no Python test file was planned."

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