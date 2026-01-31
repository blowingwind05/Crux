"""
Config Router - 配置相关路由
"""

from fastapi import APIRouter

from src.crux import CruxConfig
from backend.models import ConfigResponse
from backend.core import get_settings

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config/default", response_model=ConfigResponse)
async def get_default_config():
    """获取默认配置"""
    settings = get_settings()
    config = CruxConfig()
    
    return ConfigResponse(
        data_source_type=config.data_source_type,
        data_source_path=settings.default_data_source_path,
        schema_path=config.schema_path or settings.default_schema_path,
        mock_llm=config.mock_llm,
        debug=config.debug,
        llm={
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
        },
        search={
            "max_iterations": config.search.max_iterations,
            "top_k": config.search.top_k,
            "use_bm25": config.search.use_bm25,
            "use_vector": config.search.use_vector,
            "use_metadata_filter": config.search.use_metadata_filter,
        }
    )
