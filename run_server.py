"""
Server runner script for AI Document Generation Engine.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main.py:app", host="127.0.0.1", port=8000, reload=True)
