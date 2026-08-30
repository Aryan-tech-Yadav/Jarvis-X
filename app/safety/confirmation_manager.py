class ConfirmationManager:
    
    def needs_confirmation(self, intent):
        
        dangerous = [           
            
            "DELETE_FILE",
            
            "DELETE_FOLDER",
            
            "SHOUTDOWN",
            
            "RESTART"
        ]
        
        return intent in dangerous
    
    def confirm(self):
        
        choice = input ("Continue? (Y/N): ")
        
        return choice.lower() == "y"