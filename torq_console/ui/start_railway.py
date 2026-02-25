import os
import uvicorn

def main():
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        "torq_console.ui.railway_app:app",
        host="0.0.0.0",
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )

if __name__ == "__main__":
    main()

# Trigger Railway auto-deploy
