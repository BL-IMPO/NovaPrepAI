import os
from django.db import connection
from django.core.exceptions import ImproperlyConfigured
from contextlib import contextmanager


@contextmanager
def get_django_db():
    """
    Context manager to ensure Django database connection is properly closed.
    """
    try:
        yield connection
    finally:
        connection.close()

def check_django_db():
    """
    Check if Django database if properly configured.
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

#load_dotenv()
#
#DB_USER = os.getenv("POSTGRES_USER", "postgres")
#DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
#DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
#DB_PORT = os.getenv("POSTGRES_PORT", "5432")
#DB_NAME = os.getenv("POSTGRES_DB", "postgres")
#
#DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#
#engine = create_engine(DATABASE_URL)
#SessionLocal = sessionmaker(bind=engine)
#
#Base = declarative_base()