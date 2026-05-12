from app.controllers.auth_controller import router as auth_router
from app.controllers.user_controller import router as user_router
from app.controllers.dashboard_controller import router as dashboard_router

def register_routes(app):
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(dashboard_router)