import os
import secrets
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

OPERATOR_USER = os.getenv("MOCK_OPERATOR_USER")
OPERATOR_PASS = os.getenv("MOCK_OPERATOR_PASS")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI()

SESSIONS: dict[str, float] = {}

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == OPERATOR_USER and password == OPERATOR_PASS:
        token = secrets.token_hex(16)
        SESSIONS[token] = time.time()
        response = RedirectResponse("/search", status_code=303)
        response.set_cookie("session", value=token, httponly=True)
        return response
    
    return templates.TemplateResponse(request, "login.html", {"error": "Invalid username or password."})
