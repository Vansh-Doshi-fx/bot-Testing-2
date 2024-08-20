import openai
import os
from openai import OpenAI
from dotenv import load_dotenv
import re
from generate_file_name_and_extension import generate_FileName_and_extension
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

def create_new_file(prompt, repo_dir):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant that creates new code files based on user prompts."
                "Create a new file with the functionality described in the prompt."
                "Strictly do not include the main function or any call to it in the new file."
                "Provide the full content of the file, including necessary imports and code structure."
                "Do not add any comments or code blocks that start with '''python''' or any other programming language."
                "If the prompt is related to creating requirements file then simply create a requirements.txt file with libraries asked in the prompt.Also dont include requirements.txt in the code."
            )
        },
        {
            "role": "user",
            "content": f"Create a new file with the following functionality: {prompt}"
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
    new_file_content = response.choices[0].message.content
    # Remove the main function if it exists
    # new_file_content = re.sub(r'\nif __name__ == "__main__":\n(    .+\n)+', '', new_file_content)
    file_name, file_extension = generate_FileName_and_extension(new_file_content)
    if file_extension:
        file_path = os.path.join(repo_dir, f"{file_name}.{file_extension}")
    else:
        file_path = os.path.join(repo_dir, file_name)
    with open(file_path, "w") as f:
        f.write(new_file_content)
    return file_path