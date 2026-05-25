import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    VECTOR_DB_PATH = "vector_db"
