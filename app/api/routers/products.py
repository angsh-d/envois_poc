"""
Products API Router.

Provides endpoints to retrieve product information for the landing page.
Products can be either:
1. Pre-configured default products (like DELTA TT)
2. Products configured through onboarding sessions
"""
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.database_service import get_database_service

router = APIRouter()


class Product(BaseModel):
    """Product information model."""
    id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    description: str = Field(..., description="Product description")
    status: Literal["active", "configured", "pending"] = Field(
        ..., description="Product configuration status"
    )
    indication: str = Field(..., description="Clinical indication")
    study_phase: Optional[str] = Field(None, description="Current study phase")
    study_id: Optional[str] = Field(None, description="Associated study ID")
    data_last_updated: Optional[str] = Field(None, description="Last data update timestamp")


class ProductsResponse(BaseModel):
    """Products list response."""
    success: bool = True
    products: List[Product]
    total: int
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Pre-configured default products with real data
DEFAULT_PRODUCTS = [
    Product(
        id="delta-tt",
        name="DELTA TT Revision Cup",
        category="Hip Reconstruction",
        description="Trabecular Titanium acetabular cup for revision hip arthroplasty with enhanced osseointegration",
        status="active",
        indication="Revision THA",
        study_phase="Post-Market (H-34)",
        study_id="h34-delta",
        data_last_updated=datetime.utcnow().isoformat(),
    ),
]


@router.get(
    "/products",
    response_model=ProductsResponse,
    summary="Get all products",
    description="Retrieve all configured products for the landing page",
)
async def get_products() -> ProductsResponse:
    """
    Get all products for the landing page.

    Returns both pre-configured default products and products
    configured through onboarding sessions.
    """
    products = list(DEFAULT_PRODUCTS)

    # Get onboarded products from database
    try:
        db_service = get_database_service()
        sessions = db_service.list_sessions(limit=50)

        for session in sessions:
            # Get full session data
            full_session = db_service.get_session(session["session_id"])
            if not full_session:
                continue

            # Skip if this is the default DELTA TT product
            if full_session.get("protocol_id") == "H-34":
                continue

            # Determine status based on session state
            status: Literal["active", "configured", "pending"]
            if full_session.get("completed_at"):
                status = "configured"
            elif full_session.get("current_phase") == "complete":
                status = "configured"
            else:
                status = "pending"

            product = Product(
                id=full_session.get("protocol_id", session["session_id"]).lower().replace(" ", "-"),
                name=full_session.get("product_name", "Unknown Product"),
                category=full_session.get("category", "Medical Device"),
                description=f"Clinical study for {full_session.get('indication', 'medical device')}",
                status=status,
                indication=full_session.get("indication", ""),
                study_phase=full_session.get("study_phase"),
                study_id=session["session_id"],
                data_last_updated=full_session.get("updated_at"),
            )
            products.append(product)
    except Exception:
        # If database fails, just return default products
        pass

    return ProductsResponse(
        success=True,
        products=products,
        total=len(products),
    )


@router.get(
    "/products/{product_id}",
    response_model=Product,
    summary="Get product details",
    description="Retrieve details for a specific product",
)
async def get_product(product_id: str) -> Product:
    """Get details for a specific product."""
    # Check default products
    for product in DEFAULT_PRODUCTS:
        if product.id == product_id:
            return product

    # Check onboarded products
    try:
        db_service = get_database_service()
        session = db_service.get_session(product_id)
        if session:
            status: Literal["active", "configured", "pending"]
            if session.get("completed_at"):
                status = "configured"
            elif session.get("current_phase") == "complete":
                status = "configured"
            else:
                status = "pending"

            return Product(
                id=session.get("protocol_id", product_id).lower().replace(" ", "-"),
                name=session.get("product_name", "Unknown Product"),
                category=session.get("category", "Medical Device"),
                description=f"Clinical study for {session.get('indication', 'medical device')}",
                status=status,
                indication=session.get("indication", ""),
                study_phase=session.get("study_phase"),
                study_id=product_id,
                data_last_updated=session.get("updated_at"),
            )
    except Exception:
        pass

    # Return a pending placeholder for unknown products
    return Product(
        id=product_id,
        name=product_id.replace("-", " ").title(),
        category="Medical Device",
        description="Product configuration required",
        status="pending",
        indication="",
        study_phase=None,
        study_id=None,
        data_last_updated=None,
    )


@router.get(
    "/products/data-timestamp",
    summary="Get data last updated timestamp",
    description="Get the timestamp of the most recent data update",
)
async def get_data_timestamp() -> dict:
    """Get the timestamp of the most recent data update."""
    # For now, return current timestamp
    # In production, this would query the actual data update time
    return {
        "last_updated": datetime.utcnow().isoformat(),
        "formatted": datetime.utcnow().strftime("%b %d, %Y"),
    }