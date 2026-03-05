#!/usr/bin/env python3
"""
Railway entrypoint - reads PORT from environment and starts uvicorn.
This wrapper avoids shell expansion issues with $PORT on Railway.
"""
import os
import uvicorn

def main():
    # Railway provides PORT as environment variable
    port_raw = os.getenv("PORT", "8000")
    try:
        port = int(port_raw)
    except ValueError:
        port = 8000

    log_level = os.getenv("LOG_LEVEL", "warning").lower()

    print(f"Starting Railway app on port {port}...", flush=True)

    uvicorn.run(
        "railway_app:app",  # Use the standalone railway_app module
        host="0.0.0.0",
        port=port,
        log_level=log_level,
    )

if __name__ == "__main__":
    main()
