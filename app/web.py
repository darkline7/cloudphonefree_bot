"""FastAPI Admin Web Dashboard and REST API."""

import asyncio
import logging
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
import os

from app.config import settings
from app.dependencies import container

logger = logging.getLogger(__name__)

web_app = FastAPI(title="UmoCloud Bot Dashboard", docs_url=None, redoc_url=None)
web_app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Pydantic Schemas for API
class LoginRequest(BaseModel):
    username: str
    password: str

class BroadcastRequest(BaseModel):
    content: str
    target_user_id: Optional[int] = None

class UpdateBonusRequest(BaseModel):
    bonus_turns: int

class DirectMessageRequest(BaseModel):
    content: str

class UpdateBalanceRequest(BaseModel):
    balance: int

class ProductCreateRequest(BaseModel):
    name: str
    price: int
    description: Optional[str] = None

class ProductUpdateRequest(BaseModel):
    name: str
    price: int
    description: Optional[str] = None
    is_active: bool = True

class AddStockRequest(BaseModel):
    items: List[str]

def is_authenticated(request: Request) -> bool:
    """Check if current web session is logged in."""
    return request.session.get("authenticated", False) is True

def login_required(request: Request):
    """Dependency to protect routes and API."""
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập hoặc phiên làm việc đã hết hạn",
        )

# ==================== REST API ROUTES ====================

@web_app.post("/api/auth/login")
async def api_login(request: Request, body: LoginRequest):
    """API endpoint for login."""
    if body.username == settings.WEB_USERNAME and body.password == settings.WEB_PASSWORD:
        request.session["authenticated"] = True
        return {"success": True, "message": "Đăng nhập thành công"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sai tên đăng nhập hoặc mật khẩu!")

@web_app.post("/api/auth/logout")
async def api_logout(request: Request):
    """API endpoint for logout."""
    request.session.clear()
    return {"success": True, "message": "Đã đăng xuất"}

@web_app.get("/api/auth/me")
async def api_me(request: Request):
    """Check auth status."""
    return {
        "authenticated": is_authenticated(request),
        "username": settings.WEB_USERNAME if is_authenticated(request) else None,
    }

@web_app.get("/api/dashboard/stats")
async def api_dashboard_stats(_: None = Depends(login_required)):
    """Fetch dashboard overall metrics and statistics."""
    stats = await container.account_repo.get_statistics()
    users = await container.user_repo.get_all_users()
    accounts = await container.account_repo.get_all_accounts()

    total_bonus_awarded = sum(u.bonus_turns for u in users)
    total_trials = sum(1 for a in accounts if a.get("trial_received") == 1)

    return {
        "total_accounts": stats.get("total", 0),
        "total_users": len(users),
        "total_trials": total_trials,
        "total_bonus_awarded": total_bonus_awarded,
        "environment": settings.ENVIRONMENT,
        "settings": {
            "default_quota": 10,
            "referral_reward": 5,
            "required_chat_id": settings.REQUIRED_CHAT_ID,
            "required_chat_url": settings.REQUIRED_CHAT_URL,
        }
    }




@web_app.get("/api/users")
async def api_get_users(_: None = Depends(login_required)):
    """Fetch all users list."""
    users = await container.user_repo.get_all_users()
    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "first_name": u.first_name,
            "referrer_id": u.referrer_id,
            "bonus_turns": u.bonus_turns,
            "created_at": str(u.created_at),
            "last_seen_at": str(u.last_seen_at),
        }
        for u in users
    ]

@web_app.put("/api/users/{user_id}/bonus")
async def api_update_user_bonus(user_id: int, body: UpdateBonusRequest, _: None = Depends(login_required)):
    """Update bonus turns for a user."""
    if body.bonus_turns < 0:
        raise HTTPException(status_code=400, detail="Lượt thưởng không thể âm")
    await container.user_repo.set_bonus_turns(user_id, body.bonus_turns)
    return {"success": True, "message": f"Đã cập nhật lượt thưởng cho user {user_id} thành {body.bonus_turns}"}

@web_app.delete("/api/users/{user_id}")
async def api_delete_user(user_id: int, _: None = Depends(login_required)):
    """Delete a user."""
    await container.user_repo.delete_user(user_id)
    return {"success": True, "message": f"Đã xoá user {user_id}"}

@web_app.post("/api/users/{user_id}/message")
async def api_send_direct_message(user_id: int, body: DirectMessageRequest, _: None = Depends(login_required)):
    """Send a direct message to a specific user via Telegram bot."""
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Nội dung không được để trống")
    
    from app.main import get_bot_instance
    bot = get_bot_instance()
    if not bot:
        raise HTTPException(status_code=503, detail="Telegram Bot chưa sẵn sàng")
    
    try:
        await bot.send_message(chat_id=user_id, text=f"🔔 <b>Tin nhắn từ Quản Trị Viên:</b>\n\n{body.content.strip()}", parse_mode="HTML")
        return {"success": True, "message": f"Đã gửi tin nhắn tới user {user_id}"}
    except Exception as e:
        logger.error("Failed to send direct message to user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail=f"Gửi thất bại: {str(e)}")

@web_app.get("/api/accounts")
async def api_get_accounts(_: None = Depends(login_required)):
    """Fetch all generated accounts."""
    accounts = await container.account_repo.get_all_accounts()
    return accounts

@web_app.delete("/api/accounts/{account_id}")
async def api_delete_account(account_id: int, _: None = Depends(login_required)):
    """Delete an account record."""
    await container.account_repo.delete_account(account_id)
    return {"success": True, "message": f"Đã xoá bản ghi tài khoản #{account_id}"}


@web_app.post("/api/accounts/generate")
async def api_generate_account(_: None = Depends(login_required)):
    """Admin feature: manually trigger account creation."""
    try:
        email, password, api_user_id, token, cuid = await container.account_service.create_account()
        account_id = await container.account_repo.record_created_account(
            user_id=0,
            username="Admin Web",
            email=email,
            api_user_id=api_user_id,
        )
        return {
            "success": True,
            "account": {
                "id": account_id,
                "email": email,
                "password": password,
                "api_user_id": api_user_id,
            }
        }
    except Exception as e:
        logger.exception("Web admin account generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Tạo tài khoản thất bại: {str(e)}")

@web_app.post("/api/broadcast")
async def api_broadcast(body: BroadcastRequest, _: None = Depends(login_required)):
    """Broadcast announcement to Telegram users."""
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Nội dung thông báo không được để trống")

    if body.target_user_id:
        target_ids = [body.target_user_id]
    else:
        target_ids = await container.user_repo.get_all_user_ids()

    if not target_ids:
        raise HTTPException(status_code=400, detail="Không có người dùng nào để gửi")

    async def do_broadcast():
        success_count = 0
        fail_count = 0
        broadcast_msg = f"📢 <b>Thông báo từ Admin:</b>\n\n{content}"

        from app.main import get_bot_instance
        bot = get_bot_instance()
        if not bot:
            logger.error("Bot instance not available for broadcast.")
            return

        for uid in target_ids:
            try:
                await bot.send_message(chat_id=uid, text=broadcast_msg, parse_mode="HTML")
                success_count += 1
            except Exception:
                fail_count += 1
            await asyncio.sleep(0.05)
        logger.info("Broadcast finished: %d success, %d failed", success_count, fail_count)

    asyncio.create_task(do_broadcast())
    return {
        "success": True,
        "message": f"Đang tiến hành gửi thông báo tới {len(target_ids)} người dùng",
        "target_count": len(target_ids),
    }

@web_app.post("/api/users/{user_id}/balance")
async def api_update_user_balance(user_id: int, body: UpdateBalanceRequest, _: None = Depends(login_required)):
    """Update a user's wallet balance."""
    await container.user_repo.set_balance(user_id=user_id, balance=body.balance)
    return {"success": True, "message": f"Cập nhật số dư thành công: {body.balance:,}đ"}

@web_app.get("/api/products")
async def api_get_products(_: None = Depends(login_required)):
    """Fetch all products with stock counts."""
    products = await container.shop_repo.get_all_products(active_only=False)
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "description": p.description,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "stock_count": p.stock_count,
        }
        for p in products
    ]

@web_app.post("/api/products")
async def api_create_product(body: ProductCreateRequest, _: None = Depends(login_required)):
    """Create a new product."""
    p_id = await container.shop_repo.create_product(
        name=body.name,
        price=body.price,
        description=body.description,
    )
    return {"success": True, "product_id": p_id}

@web_app.put("/api/products/{product_id}")
async def api_update_product(product_id: int, body: ProductUpdateRequest, _: None = Depends(login_required)):
    """Update existing product."""
    await container.shop_repo.update_product(
        product_id=product_id,
        name=body.name,
        price=body.price,
        description=body.description,
        is_active=body.is_active,
    )
    return {"success": True}

@web_app.delete("/api/products/{product_id}")
async def api_delete_product(product_id: int, _: None = Depends(login_required)):
    """Delete a product and its unsold inventory."""
    await container.shop_repo.delete_product(product_id)
    return {"success": True}

@web_app.get("/api/products/{product_id}/stock")
async def api_get_product_stock(product_id: int, _: None = Depends(login_required)):
    """Get stock inventory items for a product."""
    items = await container.shop_repo.get_stock_items(product_id=product_id, unsold_only=False)
    return [
        {
            "id": i.id,
            "product_id": i.product_id,
            "data": i.data,
            "is_sold": i.is_sold,
            "order_id": i.order_id,
            "created_at": i.created_at,
        }
        for i in items
    ]

@web_app.post("/api/products/{product_id}/stock")
async def api_add_product_stock(product_id: int, body: AddStockRequest, _: None = Depends(login_required)):
    """Bulk import stock lines to a product."""
    added = await container.shop_repo.add_stock_items(product_id=product_id, items=body.items)
    return {"success": True, "added_count": added}

@web_app.get("/api/orders")
async def api_get_orders(_: None = Depends(login_required)):
    """Get all shop purchase orders."""
    orders = await container.shop_repo.get_all_orders()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "username": o.username,
            "product_id": o.product_id,
            "product_name": o.product_name,
            "price": o.price,
            "account_data": o.account_data,
            "created_at": o.created_at,
        }
        for o in orders
    ]

@web_app.get("/api/bank/transactions")
async def api_get_bank_transactions(_: None = Depends(login_required)):
    """Get all recorded bank deposit transactions."""
    txs = await container.bank_repo.get_all_transactions()
    return [
        {
            "id": t.id,
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "description": t.description,
            "transaction_date": t.transaction_date,
            "user_id": t.user_id,
            "created_at": t.created_at,
        }
        for t in txs
    ]

@web_app.post("/api/bank/sync")
async def api_sync_bank(_: None = Depends(login_required)):
    """Trigger manual bank polling synchronization."""
    processed = await container.bank_service.check_transactions()
    return {"success": True, "processed_count": processed}

# ==================== STATIC & SPA FALLBACK ====================
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "dist")

if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        web_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@web_app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve SPA index.html or static files."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    file_path = os.path.join(DIST_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    index_html = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
    
    return HTMLResponse(
        content="<h1>Frontend build is missing. Please run `npm run build` in frontend directory.</h1>",
        status_code=503,
    )

