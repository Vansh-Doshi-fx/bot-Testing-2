from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ResyncRequest(BaseModel):
    github_url: str
    access_token: str

@app.post("/resync")
async def resync(request: ResyncRequest):
    try:
        # Here you would call the existing resync functionality from main.py
        # For example: result = main.resync_function(request.github_url, request.access_token)
        
        # Simulating the resync process
        result = True  # This should be replaced with the actual call to the resync functionality
        
        if result:
            return {"message": "Resync successful"}
        else:
            raise HTTPException(status_code=400, detail="Resync failed due to an unknown error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))