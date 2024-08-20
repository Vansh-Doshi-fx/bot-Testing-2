from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

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