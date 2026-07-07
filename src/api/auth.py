"""
User authentication module for Badminton AI Coach.
Supports:
  - Username/password register & login
  - WeChat Mini-Program login (code2session)
  - Token-based session auth (Bearer token in Authorization header)
  - Profile management
"""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "users.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

WECHAT_APPID = os.environ.get("WECHAT_APPID", "wxa62a3ae0f2c7c0f4")
WECHAT_SECRET = os.environ.get("WECHAT_SECRET", "")
WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

TOKEN_EXPIRY_DAYS = 30


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            nickname TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            avatar TEXT DEFAULT '',
            wechat_openid TEXT UNIQUE,
            wechat_unionid TEXT,
            wechat_session_key TEXT,
            language TEXT DEFAULT 'zh',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            device TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_users_openid ON users(wechat_openid);
    """)
    conn.commit()
    conn.close()


_init_db()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()


def _make_token() -> str:
    return secrets.token_hex(32)


def _now() -> int:
    return int(time.time())


def _user_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"] or "",
        "nickname": row["nickname"],
        "avatar": row["avatar"] or "",
        "has_wechat": bool(row["wechat_openid"]),
        "language": row["language"] or "zh",
        "created_at": row["created_at"],
    }


def create_user(username: str, password: str, nickname: str = "", email: str = "") -> dict:
    if not username or len(username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2个字符")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    nickname = nickname or username
    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="用户名已存在")
        if email:
            existing_email = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing_email:
                raise HTTPException(status_code=409, detail="邮箱已注册")
        salt = secrets.token_hex(16)
        pw_hash = _hash_password(password, salt)
        now = _now()
        cur = conn.execute(
            "INSERT INTO users (username, email, nickname, password_hash, salt, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, email or None, nickname, pw_hash, salt, now, now),
        )
        user_id = cur.lastrowid
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_to_dict(row)
    finally:
        conn.close()


def verify_password(username: str, password: str) -> dict:
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        pw_hash = _hash_password(password, row["salt"])
        if not hmac.compare_digest(pw_hash, row["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        return _user_to_dict(row)
    finally:
        conn.close()


def create_session(user_id: int, device: str = "web") -> str:
    token = _make_token()
    now = _now()
    expires = now + TOKEN_EXPIRY_DAYS * 86400
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at, device) VALUES (?, ?, ?, ?, ?)",
            (token, user_id, now, expires, device),
        )
        conn.commit()
    finally:
        conn.close()
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ? AND s.expires_at > ?",
            (token, _now()),
        ).fetchone()
        return _user_to_dict(row) if row else None
    finally:
        conn.close()


def delete_session(token: str):
    if token.startswith("Bearer "):
        token = token[7:]
    conn = _get_db()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()


def delete_all_user_sessions(user_id: int, except_token: str = ""):
    conn = _get_db()
    try:
        if except_token:
            conn.execute("DELETE FROM sessions WHERE user_id = ? AND token != ?", (user_id, except_token))
        else:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def wechat_miniprogram_login(js_code: str, nickname: str = "", avatar: str = "") -> dict:
    import hashlib
    if not WECHAT_SECRET:
        dev_openid = "dev_" + hashlib.md5(js_code.encode()).hexdigest()[:16]
        openid = dev_openid
        unionid = ""
        session_key = "dev_session"
    else:
        params = {
            "appid": WECHAT_APPID,
            "secret": WECHAT_SECRET,
            "js_code": js_code,
            "grant_type": "authorization_code",
        }
        try:
            resp = requests.get(WECHAT_CODE2SESSION_URL, params=params, timeout=10)
            data = resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"微信接口请求失败: {e}")
        if "openid" not in data:
            errcode = data.get("errcode", -1)
            errmsg = data.get("errmsg", "unknown")
            raise HTTPException(status_code=401, detail=f"微信登录失败: {errcode} {errmsg}")
        openid = data["openid"]
        unionid = data.get("unionid", "")
        session_key = data.get("session_key", "")
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE wechat_openid = ?", (openid,)).fetchone()
        now = _now()
        if row:
            updates = ["wechat_session_key = ?", "wechat_unionid = COALESCE(NULLIF(?, ''), wechat_unionid)", "updated_at = ?"]
            values = [session_key, unionid, now]
            # Update nickname/avatar from WeChat only if user hasn't manually set a custom one
            # and the new values are non-empty. Prefer WeChat-provided info over defaults.
            default_nicknames = ("wx_", "羽毛球爱好者", "微信用户")
            is_default_nickname = any(row["nickname"].startswith(p) for p in default_nicknames if p != "微信用户") or row["nickname"] == "微信用户"
            if nickname and nickname.strip() and is_default_nickname:
                updates.append("nickname = ?")
                values.append(nickname.strip())
            if avatar and avatar.strip() and not row["avatar"]:
                updates.append("avatar = ?")
                values.append(avatar.strip())
            values.append(row["id"])
            conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
            user_id = row["id"]
            user_dict = _user_to_dict(row)
        else:
            auto_username = f"wx_{openid[-8:]}"
            base_username = auto_username
            suffix = 1
            while conn.execute("SELECT id FROM users WHERE username = ?", (auto_username,)).fetchone():
                auto_username = f"{base_username}_{suffix}"
                suffix += 1
            salt = secrets.token_hex(16)
            random_pw = secrets.token_hex(16)
            pw_hash = _hash_password(random_pw, salt)
            cur = conn.execute(
                "INSERT INTO users (username, nickname, password_hash, salt, wechat_openid, wechat_unionid, wechat_session_key, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (auto_username, nickname or f"羽毛球爱好者{openid[-4:]}", pw_hash, salt, openid, unionid or None, session_key, now, now),
            )
            user_id = cur.lastrowid
            if avatar:
                conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            user_dict = _user_to_dict(row)
    finally:
        conn.close()
    token = create_session(user_id, device="miniprogram")
    return {"user": user_dict, "token": token, "is_new": user_dict["username"].startswith("wx_")}


def update_user_profile(user_id: int, nickname: str = None, avatar: str = None, language: str = None) -> dict:
    conn = _get_db()
    try:
        fields = []
        values = []
        if nickname is not None:
            if len(nickname) < 1:
                raise HTTPException(status_code=400, detail="昵称不能为空")
            fields.append("nickname = ?")
            values.append(nickname)
        if avatar is not None:
            fields.append("avatar = ?")
            values.append(avatar)
        if language is not None:
            fields.append("language = ?")
            values.append(language)
        if not fields:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _user_to_dict(row)
        fields.append("updated_at = ?")
        values.append(_now())
        values.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_to_dict(row)
    finally:
        conn.close()


def bind_wechat(user_id: int, js_code: str) -> dict:
    import hashlib
    if not WECHAT_SECRET:
        openid = "dev_" + hashlib.md5(js_code.encode()).hexdigest()[:16]
        session_key = "dev_session"
    else:
        params = {
            "appid": WECHAT_APPID,
            "secret": WECHAT_SECRET,
            "js_code": js_code,
            "grant_type": "authorization_code",
        }
        try:
            resp = requests.get(WECHAT_CODE2SESSION_URL, params=params, timeout=10)
            data = resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"微信接口请求失败: {e}")
        if "openid" not in data:
            raise HTTPException(status_code=401, detail=f"微信绑定失败: {data.get('errmsg', 'unknown')}")
        openid = data["openid"]
        session_key = data.get("session_key", "")
    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE wechat_openid = ? AND id != ?", (openid, user_id)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="该微信已绑定其他账号")
        conn.execute(
            "UPDATE users SET wechat_openid = ?, wechat_session_key = ?, updated_at = ? WHERE id = ?",
            (openid, session_key, _now(), user_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_to_dict(row)
    finally:
        conn.close()


def unbind_wechat(user_id: int) -> dict:
    conn = _get_db()
    try:
        conn.execute("UPDATE users SET wechat_openid = NULL, wechat_session_key = NULL, updated_at = ? WHERE id = ?", (_now(), user_id))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_to_dict(row)
    finally:
        conn.close()


def change_password(user_id: int, old_password: str, new_password: str):
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        old_hash = _hash_password(old_password, row["salt"])
        if not hmac.compare_digest(old_hash, row["password_hash"]):
            raise HTTPException(status_code=401, detail="原密码错误")
        new_salt = secrets.token_hex(16)
        new_hash = _hash_password(new_password, new_salt)
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ?, updated_at = ? WHERE id = ?",
            (new_hash, new_salt, _now(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


# ---- FastAPI Router ----

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterReq(BaseModel):
    username: str
    password: str
    nickname: str = ""
    email: str = ""


class LoginReq(BaseModel):
    username: str
    password: str


class WechatLoginReq(BaseModel):
    js_code: str
    nickname: str = ""
    avatar: str = ""


class BindWechatReq(BaseModel):
    js_code: str


class ProfileReq(BaseModel):
    nickname: str = None
    avatar: str = None
    language: str = None


class ChangePwReq(BaseModel):
    old_password: str
    new_password: str


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    user = get_user_by_token(authorization or "")
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user


@router.post("/register")
async def api_register(req: RegisterReq):
    user = create_user(req.username.strip(), req.password, req.nickname.strip(), req.email.strip())
    token = create_session(user["id"])
    return {"user": user, "token": token}


@router.post("/login")
async def api_login(req: LoginReq):
    user = verify_password(req.username.strip(), req.password)
    token = create_session(user["id"])
    return {"user": user, "token": token}


@router.post("/wechat/miniprogram-login")
async def api_wechat_login(req: WechatLoginReq):
    result = wechat_miniprogram_login(req.js_code, req.nickname, req.avatar)
    return result


@router.get("/me")
async def api_me(user: dict = Depends(get_current_user)):
    return user


@router.post("/logout")
async def api_logout(authorization: Optional[str] = Header(None)):
    if authorization:
        delete_session(authorization)
    return {"ok": True}


@router.put("/profile")
async def api_update_profile(req: ProfileReq, user: dict = Depends(get_current_user)):
    updated = update_user_profile(
        user["id"],
        nickname=req.nickname,
        avatar=req.avatar,
        language=req.language,
    )
    return updated


@router.post("/avatar")
async def api_upload_avatar(avatar: UploadFile = File(...), user: dict = Depends(get_current_user)):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    content_type = avatar.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WebP/GIF 图片")
    suffix = Path(avatar.filename or "avatar.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = ".jpg"
    avatar_dir = ROOT / "outputs" / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    stem = secrets.token_hex(8)
    avatar_path = avatar_dir / f"{stem}{suffix}"
    data = await avatar.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="头像大小不能超过 5MB")
    with open(avatar_path, "wb") as f:
        f.write(data)
    avatar_url = f"/api/auth/avatar/{avatar_path.name}"
    updated = update_user_profile(user["id"], avatar=avatar_url)
    return {"avatar_url": avatar_url, "user": updated}


@router.get("/avatar/{filename}")
async def api_get_avatar(filename: str):
    avatar_dir = ROOT / "outputs" / "avatars"
    avatar_path = (avatar_dir / filename).resolve()
    try:
        avatar_path.relative_to(avatar_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid avatar path") from exc
    if not avatar_path.exists():
        raise HTTPException(status_code=404, detail="Avatar not found")
    media_type = "image/jpeg"
    if avatar_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif avatar_path.suffix.lower() == ".webp":
        media_type = "image/webp"
    elif avatar_path.suffix.lower() == ".gif":
        media_type = "image/gif"
    return FileResponse(str(avatar_path), media_type=media_type)


@router.post("/change-password")
async def api_change_password(req: ChangePwReq, user: dict = Depends(get_current_user)):
    change_password(user["id"], req.old_password, req.new_password)
    return {"ok": True}


@router.post("/wechat/bind")
async def api_bind_wechat(req: BindWechatReq, user: dict = Depends(get_current_user)):
    updated = bind_wechat(user["id"], req.js_code)
    return updated


@router.post("/wechat/unbind")
async def api_unbind_wechat(user: dict = Depends(get_current_user)):
    updated = unbind_wechat(user["id"])
    return updated


@router.post("/logout-all")
async def api_logout_all(authorization: Optional[str] = Header(None), user: dict = Depends(get_current_user)):
    token = (authorization or "").replace("Bearer ", "") if authorization else ""
    delete_all_user_sessions(user["id"], except_token=token)
    return {"ok": True}
