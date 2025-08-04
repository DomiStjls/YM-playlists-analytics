# app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from yandex_music import Client
from starlette.middleware.sessions import SessionMiddleware
from utils import (
    get_favorite_tracks,
    get_user_id_from_token,
    get_token_from_env,
    get_user_playlists,
    write_tracks_to_file,
    get_user_like_playlists,
    get_users_likes_artists,
    get_user_like_albums,
)

load_dotenv()
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")





def get_client(token=None):
    if not token:
        token = get_token_from_env()
    if not token:
        return None
    return Client(token).init()


# --- Routes ---


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/my", response_class=HTMLResponse)
def my_stats(request: Request):
    client = get_client()
    if not client:
        return templates.TemplateResponse(
            "my_stats.html", {"request": request, "error": True}
        )
    likes = client.users_likes_tracks().fetch_tracks()
    return templates.TemplateResponse(
        "my_stats.html", {"request": request, "tracks": likes, "error": False}
    )


@app.get("/other", response_class=HTMLResponse)
def other_stats_form(request: Request):
    return templates.TemplateResponse("other_stats_form.html", {"request": request})


@app.post("/other", response_class=HTMLResponse)
def other_stats(request: Request, user_id: str = Form(...)):
    token = get_token_from_env()
    client = get_client(token)
    playlists = client.users_playlists_list(user_id)
    tracks = playlists[0].fetch_tracks()
    session_ids = request.session.get("known_ids", [])
    if user_id not in session_ids:
        session_ids.append(user_id)
    request.session["known_ids"] = session_ids

    return templates.TemplateResponse(
        "other_stats.html", {"request": request, "user_id": user_id, "tracks": tracks}
    )


@app.get("/compare", response_class=HTMLResponse)
def compare_form(request: Request):
    return templates.TemplateResponse("compare_form.html", {"request": request})


@app.post("/compare_select", response_class=HTMLResponse)
def compare_select(request: Request, user1: str = Form(...), user2: str = Form(...)):
    client = get_client()
    pl1 = client.users_playlists_list(user1)
    pl2 = client.users_playlists_list(user2)
    return templates.TemplateResponse(
        "compare_select.html",
        {
            "request": request,
            "user1": user1,
            "user2": user2,
            "playlists1": pl1,
            "playlists2": pl2,
        },
    )


@app.post("/compare_result", response_class=HTMLResponse)
def compare_result(request: Request, pl1_id: str = Form(...), pl2_id: str = Form(...)):
    client = get_client()
    tracks1 = set(
        t.id
        for t in client.users_playlists(
            pl1_id.split(":")[0], pl1_id.split(":")[1]
        ).fetch_tracks()
    )
    tracks2 = set(
        t.id
        for t in client.users_playlists(
            pl2_id.split(":")[0], pl2_id.split(":")[1]
        ).fetch_tracks()
    )
    common = tracks1 & tracks2
    return templates.TemplateResponse(
        "compare_result.html", {"request": request, "common_count": len(common)}
    )


@app.get("/find_owner", response_class=HTMLResponse)
def find_owner_form(request: Request):
    client = get_client()
    playlists = client.users_likes_playlists()
    return templates.TemplateResponse(
        "find_owner_form.html", {"request": request, "playlists": playlists}
    )


@app.post("/find_owner_result", response_class=HTMLResponse)
def find_owner_result(request: Request, playlist_id: str = Form(...)):
    owner_id = playlist_id.split(":")[0]
    session_ids = request.session.get("known_ids", [])
    if owner_id not in session_ids:
        session_ids.append(owner_id)
    request.session["known_ids"] = session_ids

    return templates.TemplateResponse(
        "find_owner_result.html",
        {
            "request": request,
            "owner_id": owner_id,
            "known_ids": sorted(request.session["known_ids"]),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)