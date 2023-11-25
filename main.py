from contextlib import asynccontextmanager
import pathlib

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from src.conf.config import settings
from src.database.connect_db import get_session, redis_db0
from src.routes import auth, contacts, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles lifespan events.

    """
    await startup()
    yield


app = FastAPI(lifespan=lifespan)


async def startup():
    """
    Handles startup events.

    """
    await FastAPILimiter.init(redis_db0)


app.include_router(
    auth.router,
    prefix="/api",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    contacts.router,
    prefix="/api",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    users.router,
    prefix="/api",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)

origins = [f"http://{settings.api_host}:{settings.api_port}"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = pathlib.Path(__file__).resolve().parent


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Handles a GET-operation to get favicon.ico.

    :return: The favicon.ico.
    :rtype: FileResponse
    """
    return FileResponse(BASE_DIR / "static/images/favicon.ico")


@app.get(
    "/api/healthchecker",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
async def healthchecker(session: AsyncSession = Depends(get_session)):
    """
    Handles a GET-operation to '/api/healthchecker' route and checks connecting to the database.

    :param session: The database session.
    :type session: AsyncSession
    :return: The message.
    :rtype: str
    """
    try:
        stmt = select(text("0"))
        result = await session.execute(stmt)
        result = result.scalar()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "OK"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )


@app.get(
    "/",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
async def read_root():
    """
    Handles a GET-operation to root route and returns the message.

    :return: The message.
    :rtype: str
    """
    return {"message": f"{settings.api_name}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=True)