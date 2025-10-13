# FILE: run.py
import uvicorn

if __name__ == "__main__":
    """
    This is the main entry point to run the FastAPI application.
    It starts a Uvicorn server, which will host the app.
    The --reload flag automatically restarts the server when code changes.
    """
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
