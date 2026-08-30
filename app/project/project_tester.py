import ast



class ProjectTester:
    
    def __init__(self):
        pass
    
    def test(self, file_info, code):
        if file_info["type"] != "python":
            return True, "Non-Python file skipped."
        
        if not code or not code.strip():
            return False, "Generated code is empty."
            
        try:
            ast.parse(code, filename=file_info["name"])
        except (SyntaxError, TypeError, ValueError) as error:
            return False, f"{file_info['name']}: {error}"

        return True, "Code passed syntax validation."