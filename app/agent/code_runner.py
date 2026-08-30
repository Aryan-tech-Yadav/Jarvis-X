import subprocess

class CodeRunner:
    
    def run(self, path):
        
        result = subprocess.run(
            ["python", path],
            capture_output= True,
            text=True
        
    )
        
        if result.returncode == 0:
            return True, result.stdout
        
        return False, result.stderr