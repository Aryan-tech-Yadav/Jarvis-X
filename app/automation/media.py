import os 

class MediaManager:
    
    def play_music(self):
        
        music = os.path.expanduser("~/Music")
        
        os.startfile(music)
        
        return "Opening Music Folder."