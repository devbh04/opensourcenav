import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://devbhangale04_db_user:devbhangale04_db_pass@EasyGit.12345.mongodb.net/EasyGit") # just a guess on atlas uri? wait, let me just read .env
