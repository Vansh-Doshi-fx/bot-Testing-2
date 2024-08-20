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

# Function to integrate new code using OpenAI GPT-4
def generate_FileName_and_extension(code):
    openai.api_key = open_ai_key
    messages = [
        {
            "role": "system",
            "content": (
            "You are a helpful AI assistant that generates relevant file name and extension based on the code provided"
            "If the code is related to the readme file then give the file name as README.md"
            "If the code is related to the Dockerfile then name that file as Dockerfile"
            "If the code is related to the requirements then name that file as requirements.txt"
            "If the code is related to fastapi then name that file as app.py"
            "Based on this code below,give me a relevant file name for the code and the extension in this format file_name,extension strictly excluding the '.' in extension")
        },
        {
            "role": "user",
            "content": f"Here is the code based on which filename and extention is to be generated: {code}"
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
    result = response.choices[0].message.content.strip().split(",")
    if len(result) == 1:
        return result[0], ''  # return the file name and an empty extension
    return result[0], result[1]

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