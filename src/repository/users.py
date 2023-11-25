from datetime import datetime, timezone
import pickle

from libgravatar import Gravatar
from pydantic import EmailStr
from redis.asyncio.client import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from src.database.connect_db import redis_db1
from src.database.models import User
from src.schemas.users import UserModel


async def set_user_in_cache(user: User, redis_db: Redis) -> None:
    """
    Sets an user in cache.

    :param user: The user to set in cache.
    :type user: User
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: None.
    :rtype: None
    """
    await redis_db.set(f"user: {user.email}", pickle.dumps(user))
    await redis_db.expire(f"user: {user.email}", 3600)


async def get_user_by_email_from_cache(email: EmailStr, redis_db: Redis) -> User | None:
    """
    Gets an user with the specified email from cache.

    :param email: The email of the user to get.
    :type email: EmailStr
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: The user with the specified email, or None if it does not exist in cache.
    :rtype: User | None
    """
    user = await redis_db.get(f"user: {email}")
    if user:
        return pickle.loads(user)


async def get_user_by_email(email: EmailStr, session: AsyncSession) -> User | None:
    """
    Gets an user with the specified email.

    :param email: The email of the user to get.
    :type email: EmailStr
    :param session: The database session.
    :type session: AsyncSession
    :return: The user with the specified email, or None if it does not exist.
    :rtype: User | None
    """
    stmt = select(User).filter(User.email == email)
    user = await session.execute(stmt)
    return user.scalar()


async def create_user(body: UserModel, session: AsyncSession, redis_db: Redis) -> User:
    """
    Creates a new user.

    :param body: The request body with data for the user to create.
    :type body: UserModel
    :param session: The database session.
    :type session: AsyncSession
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: The newly created user.
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception:
        pass
    user = User(**body.model_dump(), avatar=avatar)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    await set_user_in_cache(user, redis_db)
    return user


async def update_refresh_token(
    user: User, token: str | None, session: AsyncSession, redis_db: Redis
) -> None:
    """
    Updates a refresh token for a specific user.

    :param user: The user to update the refresh token for.
    :type user: User
    :param token: The refresh token for the user to update or None.
    :type token: str | None
    :param session: The database session.
    :type session: AsyncSession
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: None.
    :rtype: None
    """
    user.refresh_token = token
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await set_user_in_cache(user, redis_db)


async def confirm_email(
    email: EmailStr, session: AsyncSession, redis_db: Redis
) -> None:
    """
    Confirms an email of user.

    :param email: The email of user to confirm.
    :type email: EmailStr
    :param session: The database session.
    :type session: AsyncSession
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.is_email_confirmed = True
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await set_user_in_cache(user, redis_db)


async def reset_password(
    email: EmailStr, session: AsyncSession, redis_db: Redis
) -> None:
    """
    Resets a password of user with specified email.

    :param email: The email of user to resets a password for.
    :type email: EmailStr
    :param session: The database session.
    :type session: AsyncSession
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.is_password_valid = False
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await set_user_in_cache(user, redis_db)


async def set_password(
    email: EmailStr, password: str, session: AsyncSession, redis_db: Redis
) -> None:
    """
    Sets a password of user with specified email.

    :param email: The email of user to set a password for.
    :type email: EmailStr
    :param password: The new password.
    :type password: str
    :param session: The database session.
    :type session: AsyncSession
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.password = password
    user.is_password_valid = True
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await set_user_in_cache(user, redis_db)


async def update_avatar(
    email: EmailStr, url: str, session: AsyncSession, redis_db: Redis
) -> User:
    """
    Updates an avatar of user with specified email.

    :param email: The email of user to update an avatar for.
    :type email: EmailStr
    :param url: The url of a new avatar.
    :type url: str
    :param session: The database session.
    :type session: AsyncSession
    :param redis_db: The client of Redis database.
    :type redis_db: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.avatar = url
    user.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await set_user_in_cache(user, redis_db)
    return user
