from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.scrape import router as scrape_router
from routes.tokens import router as tokens_router
from routes.export import router as export_router

app = FastAPI(
    title="StyleSync API",
    description="Transform any website into an interactive design system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)
app.include_router(tokens_router)
app.include_router(export_router)


@app.get("/")
def root():
    return {"message": "StyleSync API running", "version": "1.0.0"}


@app.on_event("startup")
async def startup():
    try:
        from db import init_db
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"DB startup warning: {e}")
