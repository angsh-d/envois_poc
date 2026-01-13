"""
Clinical Intelligence Platform - FastAPI Application
Main entry point for the API server.
"""
import os
import httpx
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask
import websockets
import asyncio

from app.config import settings
from app.api.routers import uc1_readiness, uc2_safety, uc3_deviations, uc4_risk, uc5_dashboard, health, chat, protocol_digitization

# Initialize FastAPI app
app = FastAPI(
    title="Clinical Intelligence Platform API",
    description="AI-powered clinical study analytics for H-34 DELTA Revision Cup Study",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(uc1_readiness.router, prefix="/api/v1/uc1", tags=["UC1: Regulatory Readiness"])
app.include_router(uc2_safety.router, prefix="/api/v1/uc2", tags=["UC2: Safety Signals"])
app.include_router(uc3_deviations.router, prefix="/api/v1/uc3", tags=["UC3: Protocol Deviations"])
app.include_router(uc4_risk.router, prefix="/api/v1/uc4", tags=["UC4: Risk Stratification"])
app.include_router(uc5_dashboard.router, prefix="/api/v1/uc5", tags=["UC5: Executive Dashboard"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(protocol_digitization.router, prefix="/api/v1/protocol", tags=["Protocol Digitization"])

# Vite dev server URL for proxying frontend requests
VITE_DEV_URL = os.getenv("VITE_DEV_URL", "http://127.0.0.1:5173")

# HTTP client for proxying to Vite
http_client = httpx.AsyncClient(base_url=VITE_DEV_URL, timeout=60.0)


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    settings.get_log_dir()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await http_client.aclose()


async def _proxy_request_to_vite(request: Request, path: str):
    """Internal function to proxy requests to Vite dev server."""
    url = f"/{path}"
    if request.query_params:
        url = f"{url}?{request.query_params}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body() if request.method in ["POST", "PUT", "PATCH"] else None,
        )
        
        excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        response_headers = {
            k: v for k, v in response.headers.items() 
            if k.lower() not in excluded_headers
        }
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type"),
        )
    except httpx.RequestError as e:
        return Response(content=f"Vite server not available: {e}", status_code=502)


# Explicit frontend routes - proxy to Vite dev server
@app.get("/")
async def root(request: Request):
    return await _proxy_request_to_vite(request, "")

@app.get("/study/{study_id}")
async def study_page(request: Request, study_id: str):
    return await _proxy_request_to_vite(request, f"study/{study_id}")

@app.get("/study/{study_id}/{path:path}")
async def study_subpages(request: Request, study_id: str, path: str):
    return await _proxy_request_to_vite(request, f"study/{study_id}/{path}")

@app.get("/src/{path:path}")
async def src_files(request: Request, path: str):
    return await _proxy_request_to_vite(request, f"src/{path}")

@app.get("/node_modules/{path:path}")
async def node_modules(request: Request, path: str):
    return await _proxy_request_to_vite(request, f"node_modules/{path}")

@app.get("/@vite/{path:path}")
async def vite_internal(request: Request, path: str):
    return await _proxy_request_to_vite(request, f"@vite/{path}")

@app.get("/@react-refresh")
async def react_refresh(request: Request):
    return await _proxy_request_to_vite(request, "@react-refresh")

@app.get("/vite.svg")
async def vite_svg(request: Request):
    return await _proxy_request_to_vite(request, "vite.svg")

@app.get("/assets/{path:path}")
async def assets(request: Request, path: str):
    return await _proxy_request_to_vite(request, f"assets/{path}")


@app.websocket("/")
async def websocket_proxy(websocket: WebSocket):
    """Proxy WebSocket connections to Vite dev server for HMR."""
    subprotocol = None
    if 'sec-websocket-protocol' in websocket.headers:
        subprotocol = websocket.headers['sec-websocket-protocol'].split(',')[0].strip()
    
    await websocket.accept(subprotocol=subprotocol)
    try:
        vite_ws_url = "ws://127.0.0.1:5173/"
        if websocket.query_params:
            vite_ws_url = f"{vite_ws_url}?{websocket.query_params}"
        
        ws_kwargs = {}
        if subprotocol:
            ws_kwargs['subprotocols'] = [subprotocol]
        
        async with websockets.connect(vite_ws_url, **ws_kwargs) as vite_ws:
            async def forward_to_vite():
                try:
                    async for message in websocket.iter_text():
                        await vite_ws.send(message)
                except Exception:
                    pass
            
            async def forward_to_client():
                try:
                    async for message in vite_ws:
                        await websocket.send_text(message)
                except Exception:
                    pass
            
            await asyncio.gather(forward_to_vite(), forward_to_client())
    except Exception as e:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
