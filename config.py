import os

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_CONVERSATION_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4.1')
OPENAI_REPORTING_MODEL= os.environ.get('OPENAI_REPORTING_MODEL', 'o4-mini')

# Application Configuration
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Validate required environment variables
def validate_config():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    return True