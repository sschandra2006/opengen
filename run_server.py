"""
Server runner script for OpenGen REST API & Web UI.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("opengen.api:app", host="127.0.0.1", port=8000, reload=True)
