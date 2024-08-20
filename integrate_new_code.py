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
def generate_newFile_based_code_changes(prompt, original_code, new_file_code, new_file_name):
    openai.api_key = open_ai_key
    messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful AI assistant that integrates new code files into original code seamlessly."
            "First, understand the provided original code and the new file code."
            "Strictly do not add any comments or code blocks that start with '''python''' or any other programming language."
            "Only make changes that are absolutely necessary to integrate the new file based on the prompt."
            "Strictly do not remove the comments in the original code."
            "Strictly do not remove original code."
            "Do not add import statements unless the original code is directly calling functions, classes, or variables from the new file."
            "If the new file's functionality is not required in the original code based on the prompt, do not add imports of the new file in the original code."
            "Strictly, if the new file is not required in the original code based on the prompt, return the original code as it is. Do not add anything in the original code in this scenerio."
            "Avoid adding examples, test cases, or unrelated code in the original code."
            "Maintain the integrity of the original code without introducing any unnecessary elements."
            "Strictly do not remove any imports from the original code"
            "If the function or class from the new file is not called in the original code, refrain from adding import statements."
            "Return the code as it is if no integration is necessary."
        )
    },
    {
        "role": "user",
        "content": f"Here is the current code: {original_code}\nthis is the new code in the new file: {new_file_code}\nthis is the new file name: {new_file_name}\nprompt-find hints about changes if and only if given any hints: {prompt}"
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