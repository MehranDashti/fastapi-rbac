import uvicorn
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("SERVER_LISTEN_IP", "0.0.0.0"),
        port=int(os.getenv("SERVER_LISTEN_PORT", "8000")),
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
        reload=os.getenv("PRODUCTION", "false").lower() != "true",
        loop="asyncio",
        workers=int(os.getenv("SERVER_WORKERS", "1")),
    )
