from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.routes import register_routes
from app.config.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema AAPM")

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

register_routes(app)


@app.get("/")
async def root():
    return RedirectResponse("/login")