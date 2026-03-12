import uvicorn
import sys

if __name__ == "__main__":
    port = 8092
    print(f"Starting server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
