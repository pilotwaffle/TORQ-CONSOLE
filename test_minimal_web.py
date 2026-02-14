#!/usr/bin/env python3
"""Minimal web server test"""

import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return HTMLResponse("<html><body><h1>Simple Test Works!</h1></body></html>")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("Starting minimal web server on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
