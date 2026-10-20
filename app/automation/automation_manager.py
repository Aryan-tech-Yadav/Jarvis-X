import subprocess
import time
import webbrowser

from app.core.logger import Logger
from app.automation.application import ApplicationManager
from app.automation.website import WebsiteManager
from app.automation.folder import FolderManager
from app.automation.media import MediaManager


class AutomationManager:
    """Facade for all desktop automation sub-systems.

    Delegates to specialized managers:
      - ApplicationManager: open/close desktop apps
      - WebsiteManager: open URLs in the browser
      - FolderManager: open file-explorer folders
      - MediaManager: play local media
    """

    def __init__(self):
        self.application = ApplicationManager()
        self.website = WebsiteManager()
        self.folder = FolderManager()
        self.media = MediaManager()

    def open_application(self, app: str) -> str:
        """Open a desktop application by name."""
        return self.application.open(app)

    def open_website(self, website: str) -> str:
        """Open a website in the default browser."""
        return self.website.open(website)

    def open_folder(self, folder: str) -> str:
        """Open a folder in the file explorer."""
        return self.folder.open(folder)

    def open_music(self) -> str:
        """Play music using the default media player."""
        return self.media.play_music()

    def play_spotify(self, song_name: str = ""):
        """Open Spotify and play a specific song.
        
        Args:
            song_name: Name of the song to play. If empty, asks user.
        
        Returns:
            Status message.
        """
        try:
            # Open Spotify
            spotify_result = self.application.open("spotify")
            if "Opening" not in spotify_result:
                return spotify_result

            # Wait for Spotify to fully load
            time.sleep(3)

            # If song name provided, try to play it
            if song_name:
                return self._play_song_in_spotify(song_name)
            else:
                # Return message asking for song name
                return "Spotify opened. Please tell me the song name you want to play."

        except Exception as e:
            return f"Could not control Spotify: {e}"

    def _play_song_in_spotify(self, song_name: str) -> str:
        """Play a specific song in Spotify using keyboard shortcuts.
        
        This uses pyautogui to:
        1. Focus Spotify window
        2. Search for the song (Ctrl+K)
        3. Play the song
        """
        try:
            import pyautogui
            pyautogui.FAILSAFE = True

            # Click on Spotify search box (Ctrl+K or Ctrl+L)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)

            # Type song name
            pyautogui.typewrite(song_name, interval=0.05)
            time.sleep(1)

            # Press Enter to play first result
            pyautogui.press('enter')

            return f"Playing {song_name} on Spotify."

        except ImportError:
            # Fallback: open Spotify search in browser
            try:
                webbrowser.open(f"https://open.spotify.com/search/{song_name.replace(' ', '%20')}")
                return f"Searching for {song_name} on Spotify."
            except Exception:
                return f"Spotify opened. Please search for {song_name} manually."
        except Exception as e:
            return f"Spotify opened but couldn't play song: {e}"

    def play_music(self, service="spotify", song_name: str = ""):
        """Play music on specified service."""
        if service.lower() == "spotify":
            return self.play_spotify(song_name)
        return self.media.play_music()

    def search_google(self, query: str) -> str:
        """Search Google and return summarized results."""
        try:
            from app.internet.internet_manager import InternetManager
            internet = InternetManager()
            return internet.google(query)
        except Exception as e:
            # Fallback: open browser search
            try:
                import webbrowser
                webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
                return f"Opening Google search for: {query}"
            except Exception:
                return f"Search failed: {e}"

    def get_news(self, category: str = "latest") -> str:
        """Fetch latest news and summarize."""
        try:
            from app.internet.internet_manager import InternetManager
            internet = InternetManager()
            if category and category.lower() != "latest":
                return internet.get_news() + f"\n\nAlso searching for: {category}"
            return internet.get_news()
        except Exception as e:
            return f"Could not fetch news: {e}"

    def shutdown(self, delay_seconds=30):
        """Shutdown the computer."""
        try:
            if subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], capture_output=True).returncode == 0:
                return f"Laptop will shutdown in {delay_seconds} seconds. Say 'cancel shutdown' to cancel."
            return "Failed to shutdown."
        except Exception as e:
            return f"Shutdown failed: {e}"

    def restart(self, delay_seconds=30):
        """Restart the computer."""
        try:
            if subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], capture_output=True).returncode == 0:
                return f"Laptop will restart in {delay_seconds} seconds. Say 'cancel shutdown' to cancel."
            return "Failed to restart."
        except Exception as e:
            return f"Restart failed: {e}"

    def cancel_shutdown(self):
        """Cancel scheduled shutdown/restart."""
        try:
            if subprocess.run(["shutdown", "/a"], capture_output=True).returncode == 0:
                return "Shutdown/restart cancelled."
            return "No shutdown scheduled."
        except Exception as e:
            return f"Cancel failed: {e}"

    def sleep(self):
        """Put computer to sleep."""
        try:
            # Use rundll32 to put computer to sleep
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
            return "Putting laptop to sleep..."
        except Exception as e:
            return f"Sleep failed: {e}"

    def lock(self):
        """Lock the computer."""
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "Laptop locked."
        except Exception as e:
            return f"Lock failed: {e}"

    def close_application(self, app):
        
        return self.application.close(app)
