from fastapi import FastAPI

app = FastAPI()

on = False

@app.get("/toggle")
def toggle():
    global on
    on = True
    return on