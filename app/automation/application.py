import shutil
import subprocess

from app.core.logger import Logger
from app.automation.app_registry import APP_REGISTRY


class ApplicationManager:

    def __init__(self):
        self.apps = APP_REGISTRY

    def _find_executable(self, app_name: str):

        app = app_name.lower().strip()

        # Registry aliases
        if app in self.apps:
            exe = self.apps[app]

            path = shutil.which(exe)

            if path:
                return path

            return exe

        # Direct PATH search
        path = shutil.which(app)

        if path:
            return path

        return None

    def open(self, app_name):

        executable = self._find_executable(app_name)

        if executable is None:
            Logger.warning(f"Application not found: {app_name}")
            return f"I couldn't find {app_name}."

        try:

            subprocess.Popen([executable])

            Logger.success(f"{app_name} opened successfully.")

            return f"Opening {app_name}."

        except Exception as e:

            Logger.error(str(e))

            return f"Failed to open {app_name}."

    def close(self, app_name):

        app = app_name.lower().strip()

        executable = self.apps.get(app, app)

        exe_name = executable.split("\\")[-1]

        if not exe_name.endswith(".exe"):
            exe_name += ".exe"

        try:

            subprocess.run(
                ["taskkill", "/F", "/IM", exe_name],
                capture_output=True
            )

            Logger.success(f"{app_name} closed successfully.")

            return f"Closing {app_name}."

        except Exception as e:

            Logger.error(str(e))

            return f"Failed to close {app_name}."