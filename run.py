# FILE: run.py
import uvicorn
import os

if __name__ == "__main__":
    # Hugging Face provides the port in the 'PORT' env var. Default to 7860.
    port = int(os.environ.get("PORT", 7860))

    # Host must be "0.0.0.0" to be accessible within the Docker container
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
