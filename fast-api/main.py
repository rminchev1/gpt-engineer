from fastapi import FastAPI
from app import app

def main():
    """
    Main function to run the FastAPI application.
    """
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
