import os
import google.generativeai as genai
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables (Create a .env file with your keys, or export them in your terminal)
load_dotenv()

# Replace the old os.getenv lines with your actual strings:
GEMINI_API_KEY = "AQ.Ab8RN6KLCZSDq_aNhJKky_I4GzOwh-AZ9OSkUzIS_aGN69yvAA"       # <-- Paste your actual Gemini API Key here
GOOGLE_SEARCH_API_KEY = "AIzaSyC2bHd7sjEOZd0AkJNkN1kj67Rceo98iko" # <-- Paste your Google Cloud Search Key here
GOOGLE_CSE_ID = "a1ceffc5632b447a8"               # <-- Paste your Search Engine ID (CX) here

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# 1. Define the Custom Tool (Google Search API Integration)
def google_search(query: str) -> str:
    """
    Searches Google for real-time information. 
    Use this tool when you need current data like weather, stock prices, or news.
    """
    print(f"\n[System: Searching Google for '{query}'...]")
    try:
        # Build the Custom Search API service
        service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
        
        # Execute the search request (retrieving the top 3 results for speed)
        res = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=3).execute()
        results = res.get('items', [])
        
        if not results:
            return "No search results found."
        
        # Format the top results into a string for Gemini to digest
        formatted_results = ""
        for item in results:
            formatted_results += f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\n\n"
        
        return formatted_results
        
    except Exception as e:
        return f"An error occurred during the search: {e}"


def main():
    # 2. Initialize the Gemini Model and bind the tool
    # Using gemini-1.5-flash as it is fast and highly capable of function calling
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        tools=[google_search] 
    )

    # 3. Initialize Conversation History (Memory)
    # enable_automatic_function_calling=True allows Gemini to transparently call the 
    # google_search function, read the results, and formulate a final answer.
    chat = model.start_chat(enable_automatic_function_calling=True)

    print("=========================================================")
    print("🤖 Gemini Agent Initialized (Type 'quit' or 'exit' to stop)")
    print("=========================================================\n")

    # 4. Chat Loop
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['quit', 'exit']:
            print("Ending conversation.")
            break
            
        if not user_input.strip():
            continue

        try:
            # Send message to the chat session. The chat object automatically 
            # appends this to its internal 'history' list.
            response = chat.send_message(user_input)
            print(f"\nGemini: {response.text}\n")
            
        except Exception as e:
            print(f"\n[Error communicating with Gemini: {e}]\n")

if __name__ == "__main__":
    main()