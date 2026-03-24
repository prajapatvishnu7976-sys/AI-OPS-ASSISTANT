import os

files = ['agents/planner.py', 'agents/critic.py', 'agents/verifier.py']

for file in files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add import if not exists
        if 'ChatGoogleGenerativeAI' not in content:
            content = content.replace(
                'from langchain_openai import ChatOpenAI',
                'from langchain_openai import ChatOpenAI\nfrom langchain_google_genai import ChatGoogleGenerativeAI'
            )
        
        # Replace __init__ method
        # (You can manually do this for now)
        
        print(f"✅ Updated {file}")