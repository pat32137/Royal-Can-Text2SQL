import asyncio
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()

print(os.getenv('WXO_API_ENDPOINT') )


def test_questions():
    # Your 5 questions
    questions = [
        "Your first question here",
        "Your second question here", 
        "Your third question here",
        "Your fourth question here",
        "Your fifth question here"
    ]
    
    # Get API endpoint and credentials from environment
    api_endpoint = os.getenv('WXO_API_ENDPOINT')  # Your watsonx Orchestrate API endpoint
    api_key = os.getenv('WXO_API_KEY')  # Your API key
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"Testing question {i}: {question}")
        try:
            # Use the chat completions API
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": question}]
                    }
                ]
            }
            
            response = requests.post(
                f"{api_endpoint}/api/v1/orchestrate/text2sql_stgb/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                results.append({
                    "question": question,
                    "response": response.json()
                })
                print(f"✓ Question {i} completed\n")
            else:
                print(f"✗ Question {i} failed: {response.status_code} - {response.text}\n")
                results.append({
                    "question": question,
                    "response": f"Error: {response.status_code} - {response.text}"
                })
                
        except Exception as e:
            print(f"✗ Question {i} failed: {e}\n")
            results.append({
                "question": question,
                "response": f"Error: {e}"
            })
    
    # Save results to file
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("All questions tested! Results saved to 'test_results.json'")

# Run the test
test_questions()