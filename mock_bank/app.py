import os
import secrets
import time
import time as time_module
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from mock_bank.data import MEMBERS

load_dotenv()

OPERATOR_USER = os.getenv("MOCK_OPERATOR_USER")
OPERATOR_PASS = os.getenv("MOCK_OPERATOR_PASS")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI()

SESSIONS: dict[str, float] = {}

SESSION_TIMEOUT_SECONDS = 300  # 5 minutes, used later for expiry

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

def get_session_token(request: Request) -> str | None:
    token = request.cookies.get("session")
    if not token or token not in SESSIONS:
        return None
    if time_module.time() - SESSIONS[token] > SESSION_TIMEOUT_SECONDS:
        del SESSIONS[token]
        return None
    return token

@app.get("/search")
def search_page(request: Request, popup: int = 0, crash: int = 0):
    token = get_session_token(request)
    if not token:
        return RedirectResponse("/login", status_code=303)

    if crash:
        raise HTTPException(status_code=500, detail="Internal error")

    return templates.TemplateResponse(
        request, "search.html", {"error": None, "show_popup": bool(popup)}
    )

@app.post("/search")
def search_submit(
    request: Request,
    member_id: str = Form(...),
    slow: int = 0,
):
    token = get_session_token(request)
    if not token:
        return RedirectResponse("/login", status_code=303)

    if slow:
        time_module.sleep(3)

    if not member_id.isdigit():
        return templates.TemplateResponse(
            request, "search.html", {"error": "Member ID must be numeric.", "show_popup": False}
        )

    if member_id in MEMBERS:
        return RedirectResponse(f"/detail/{member_id}", status_code=303)

    return templates.TemplateResponse(
        request, "search.html", {"error": "No member found.", "show_popup": False}
    )

@app.get("/detail/{member_id}")
def detail_page(request: Request, member_id: str):
    token = get_session_token(request)
    if not token:
        return RedirectResponse("/login", status_code=303)

    member = MEMBERS.get(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    balance_display = "{:,.2f}".format(member["balance"])
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"member_id": member_id, "member": member, "balance_display": balance_display},
    )