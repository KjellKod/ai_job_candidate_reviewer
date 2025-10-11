#!/usr/bin/env python3
"""
AI Job Candidate Reviewer

A Python application to review job applicants, their resumes, cover letters,
and make recommendations based on job descriptions using OpenAI.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Main function to test OpenAI connection with a simple example."""
    
    # Initialize OpenAI client
    # The API key will be read from OPENAI_API_KEY environment variable
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    try:
        # Test the connection with a simple completion
        response = client.chat.completions.create(
            model="gpt-4",  # Using gpt-4 instead of gpt-5 (which doesn't exist yet)
            messages=[
                {
                    "role": "user", 
                    "content": "Write a 10 line R rated extremely scary bedtime story about a unicorn."
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        print("OpenAI connection successful!")
        print("Response:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error connecting to OpenAI: {e}")
        print("Please check your API key and internet connection.")

if __name__ == "__main__":
    main()
