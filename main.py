import os
import uvicorn
from prompt_optimizer.web.app import app

# Export app for ASGI servers like uvicorn main:app
__all__ = ["app"]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
