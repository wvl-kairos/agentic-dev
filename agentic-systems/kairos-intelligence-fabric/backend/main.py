import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import documents, graph, health, ingest, knowledge, ontology, query
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.neo4j_enabled:
        from services.neo4j_connection import get_driver

        driver = await get_driver()
        logger.info("Neo4j connected: %s", settings.neo4j_uri)
    else:
        logger.info("Neo4j not configured — using in-memory graph store")

    # Initialize RAG: chunk/embed documents if ChromaDB is empty, rebuild BM25
    await _initialize_rag()

    yield
    # Shutdown
    if settings.neo4j_enabled:
        from services.neo4j_connection import close_driver

        await close_driver()


async def _initialize_rag():
    """Rebuild BM25 index from existing ChromaDB chunks. Does NOT auto-ingest documents."""
    import asyncio

    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set — skipping RAG initialization")
        return

    try:
        from services.hybrid_retriever import rebuild_bm25_index

        # Rebuild BM25 from whatever is already in ChromaDB (may be empty)
        bm25_count = await asyncio.to_thread(rebuild_bm25_index)
        logger.info("BM25 index ready with %d chunks", bm25_count)

    except Exception as e:
        logger.error("RAG initialization failed: %s", e)


_docs_url = "/docs" if settings.env == "development" else None
_redoc_url = "/redoc" if settings.env == "development" else None

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url="/openapi.json" if settings.env == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(ontology.router, prefix="/api")
