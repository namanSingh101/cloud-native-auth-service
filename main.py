#lets make it container worthy
from app.app import app

__all__ = ["app"]


#these are only used for local dev environment
# import uvicorn

# if __name__ == "__main__":
#     uvicorn.run("app.app:app", host="0.0.0.0",log_level="info", port=8000,reload=True)