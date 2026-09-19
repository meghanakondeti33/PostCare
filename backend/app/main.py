import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
from app.ai.provider import AIProviderError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("postcare")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AIProviderError)
async def ai_provider_exception_handler(request: Request, exc: AIProviderError):
    logger.error(f"AIProviderError caught in request pipeline ({exc.provider}): status={exc.status_code} msg={exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "provider": exc.provider,
            "status_code": exc.status_code
        }
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "status": "OPERATIONAL"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
