import openai
import os
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

load_dotenv()

open_ai_key=os.environ["OPENAI_API_KEY"]
model=os.environ["MODEL"]
Temperature=os.environ["TEMPERATURE"]
Max_tokens=os.environ["MAX_TOKENS"]

client=OpenAI(api_key=open_ai_key)

app = FastAPI()

class PullRequestRequest(BaseModel):
    repo_name: str
    repo_owner: str
    token: str
    source_branch: str
    destination_branch: str
    prompt: str

@app.post("/create_pull_request/")
async def create_pull_request(request: PullRequestRequest):
    headers = {
        "Authorization": f"token {request.token}",
        "Accept": "application/vnd.github.v3+json"
    }

    create_branch_url = f"https://api.github.com/repos/{request.repo_owner}/{request.repo_name}/git/refs"
    response = requests.post(create_branch_url, headers=headers, json={
        "ref": f"refs/heads/{request.source_branch}",
        "sha": request.destination_branch_sha
    })

    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Failed to create branch")

    # Here you would integrate with OpenAI to modify the code files based on the prompt
    # Assuming the changes are made and committed to the source branch

    pull_request_url = f"https://api.github.com/repos/{request.repo_owner}/{request.repo_name}/pulls"
    pull_request_data = {
        "title": f"Pull request from {request.source_branch} to {request.destination_branch}",
        "head": request.source_branch,
        "base": request.destination_branch,
        "body": request.prompt
    }

    response = requests.post(pull_request_url, headers=headers, json=pull_request_data)

    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Failed to create pull request")

    return {"message": "Pull request created successfully", "pull_request": response.json()}

# Function to generate code changes using OpenAI GPT-4
def generate_code_changes(prompt, code):
    openai.api_key = open_ai_key
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant that modifies code based on user prompts."
                "First, understand the working of the provided code . Then, make changes as per the user's prompt."
                "Strictly do not remove the old code."
                "If the prompt is related to the docstring then use google format for generating the docstring."
                "After the changes in the code ,you should write every line of the code as it is."
                "Only modify the parts of the code that are relevant to the prompt."
                "Do not remove, add, or alter anything else that is not specified in the prompt."
                "If no relevant modifications are applicable, return the code exactly as it was without changes."
                "Avoid adding comments or extra information. Do not alter, add, or remove variable names, function names, or other identifiers unless explicitly instructed."
                "Preserve the structure, formatting, and logic of the code as much as possible."
                "Ensure that the changes are precise and strictly adhere to the instructions provided in the prompt."
                "Do not modify any text or code that is not directly mentioned in the prompt."
                "Strictly Do not add any comments or code blocks that start with '''python''' or any other programming language.")
        },
        {
            "role": "user",
            "content": f"Here is the current code: {code}\nMake the following changes: {prompt}"
        }
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=float(Temperature),
        max_tokens=int(Max_tokens),
    )
    input_token = response.usage.prompt_tokens
    output_token = response.usage.completion_tokens
    with open("token_tracker.txt", "a") as tt:
        tt.write("\n Input token: " + str(input_token) + " output token: " + str(output_token))
    return response.choices[0].message.content