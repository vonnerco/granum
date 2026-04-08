from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.core.enhancer_service import EnhancementError, EnhancerService
from src.schemas.interaction import EnhanceRequest, EnhanceResponse, HistoryResponse

router = APIRouter()


def get_service(request: Request) -> EnhancerService:
    return request.app.state.enhancer_service


@router.post('/enhance', response_model=EnhanceResponse)
async def enhance_note(
    payload: EnhanceRequest,
    service: EnhancerService = Depends(get_service),
) -> EnhanceResponse:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail='Field "text" cannot be empty.')

    try:
        return await service.enhance_text(text)
    except EnhancementError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get('/history', response_model=HistoryResponse)
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    service: EnhancerService = Depends(get_service),
) -> HistoryResponse:
    return await service.get_history(page=page, page_size=page_size)
