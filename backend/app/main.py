"""GalaWatch API: admin user management and reports.

Everything here needs a signed-in user. The service_role key stays on this server only.
"""
import os
from datetime import datetime
from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import reports
from .summary import MANILA, fill_days, manila_bounds, summarize, valid_username, validate_range

EMAIL_DOMAIN = "galawatch.app"
ROLES = ("tourism", "lgu", "admin")

app = FastAPI(title="GalaWatch API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("FRONTEND_URL", "http://localhost:5173").split(",") if o.strip()],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@lru_cache
def get_sb():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def current_profile(authorization: str = Header(default=""), sb=Depends(get_sb)) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Please sign in.")
    try:
        user = sb.auth.get_user(token).user
    except Exception:
        raise HTTPException(401, "Your session is not valid. Please sign in again.")
    if user is None:
        raise HTTPException(401, "Your session is not valid. Please sign in again.")
    rows = sb.table("profiles").select("*").eq("id", user.id).limit(1).execute().data
    if not rows or not rows[0]["active"]:
        raise HTTPException(403, "This account is disabled.")
    return rows[0]


def admin_only(profile: dict = Depends(current_profile)) -> dict:
    if profile["role"] != "admin":
        raise HTTPException(403, "Only the System Admin can do this.")
    return profile


@app.get("/health")
def health():
    return {"ok": True}


# ---------------------------------------------------------------- admin: users
class NewUser(BaseModel):
    full_name: str = Field(min_length=1, max_length=80)
    username: str
    role: str
    password: str = Field(min_length=8, max_length=72)


class NewPassword(BaseModel):
    password: str = Field(min_length=8, max_length=72)


@app.post("/admin/users", status_code=201)
def create_user(body: NewUser, _admin: dict = Depends(admin_only), sb=Depends(get_sb)):
    username = body.username.strip().lower()
    if not valid_username(username):
        raise HTTPException(400, "Username: 3 to 30 letters, numbers, dot, dash or underscore.")
    if body.role not in ROLES:
        raise HTTPException(400, "Role must be tourism, lgu or admin.")
    if sb.table("profiles").select("id").eq("username", username).limit(1).execute().data:
        raise HTTPException(409, "That username is already taken.")
    try:
        created = sb.auth.admin.create_user({
            "email": f"{username}@{EMAIL_DOMAIN}", "password": body.password, "email_confirm": True,
        })
    except Exception as e:
        raise HTTPException(400, f"Could not create the login: {e}")
    uid = created.user.id
    try:
        sb.table("profiles").insert({
            "id": uid, "full_name": body.full_name.strip(), "username": username, "role": body.role,
        }).execute()
    except Exception as e:
        sb.auth.admin.delete_user(uid)  # do not leave a login without a profile
        raise HTTPException(400, f"Could not save the profile: {e}")
    return {"ok": True, "id": uid}


def _active_admin_ids(sb) -> list[str]:
    rows = sb.table("profiles").select("id").eq("role", "admin").eq("active", True).execute().data
    return [r["id"] for r in rows]


@app.delete("/admin/users/{user_id}")
def delete_user(user_id: str, admin: dict = Depends(admin_only), sb=Depends(get_sb)):
    if user_id == admin["id"]:
        raise HTTPException(400, "You cannot delete your own account.")
    target = sb.table("profiles").select("id,role,active").eq("id", user_id).limit(1).execute().data
    if not target:
        raise HTTPException(404, "User not found.")
    if target[0]["role"] == "admin" and target[0]["active"] and len(_active_admin_ids(sb)) <= 1:
        raise HTTPException(400, "You cannot delete the last active System Admin.")
    try:
        sb.auth.admin.delete_user(user_id)  # the profile row is removed with it
    except Exception as e:
        raise HTTPException(400, f"Could not delete the user: {e}")
    return {"ok": True}


@app.post("/admin/users/{user_id}/password")
def reset_password(user_id: str, body: NewPassword, _admin: dict = Depends(admin_only), sb=Depends(get_sb)):
    if not sb.table("profiles").select("id").eq("id", user_id).limit(1).execute().data:
        raise HTTPException(404, "User not found.")
    try:
        sb.auth.admin.update_user_by_id(user_id, {"password": body.password})
    except Exception as e:
        raise HTTPException(400, f"Could not change the password: {e}")
    return {"ok": True}


# -------------------------------------------------------------------- reports
@app.get("/reports")
def report(
    destination: str,
    start: str,
    end: str,
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
    profile: dict = Depends(current_profile),
    sb=Depends(get_sb),
):
    try:
        s, e = validate_range(start, end)
    except ValueError as err:
        raise HTTPException(400, str(err))

    dest = sb.table("destinations").select("id,name,region,is_live").eq("id", destination).limit(1).execute().data
    if not dest:
        raise HTTPException(404, "Destination not found.")
    if not dest[0]["is_live"]:
        raise HTTPException(400, "Only destinations with a live camera have history to report.")

    rows = (sb.table("camera_daily_summary").select("day,peak_inside,total_in,total_out")
            .eq("destination_id", destination).gte("day", s.isoformat()).lte("day", e.isoformat()).execute().data)
    days = fill_days(rows, s, e)
    summary = summarize(days)

    lo, hi = manila_bounds(s, e)
    raw = (sb.table("alerts").select("triggered_at,people_inside,limit_value,status")
           .eq("destination_id", destination).gte("triggered_at", lo).lt("triggered_at", hi)
           .order("triggered_at").limit(500).execute().data)
    alerts = [{
        "time": datetime.fromisoformat(a["triggered_at"].replace("Z", "+00:00")).astimezone(MANILA).strftime("%Y-%m-%d %H:%M"),
        "people_inside": a["people_inside"], "limit_value": a["limit_value"], "status": a["status"],
    } for a in raw]

    meta = {
        "destination_name": dest[0]["name"], "region": dest[0]["region"],
        "start": s.isoformat(), "end": e.isoformat(),
        "generated": datetime.now(MANILA).strftime("%Y-%m-%d %H:%M"), "generated_by": profile["full_name"],
    }
    if format == "xlsx":
        data = reports.build_xlsx(meta, days, summary, alerts)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        data = reports.build_pdf(meta, days, summary, alerts)
        media = "application/pdf"
    name = f"GalaWatch_{destination}_{s.isoformat()}_to_{e.isoformat()}.{format}"
    return Response(content=data, media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'})
