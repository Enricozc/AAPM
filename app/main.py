from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import register_routes
from app.routes import auth_routes, dashboard_routes, user_routes, category_routes, product_routes

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

register_routes(app)

app.include_router(category_routes.router)
app.include_router(product_routes.router)