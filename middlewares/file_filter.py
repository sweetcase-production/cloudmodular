
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
import json

class LimitUploadSize(BaseHTTPMiddleware):

    def __init__(
        self, app: ASGIApp,
        max_size: int
    ):
        super().__init__(app)
        self.max_size = max_size * (10**6) # 1MB 단위

    async def dispatch(
        self, request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        if request.method in ('POST', 'PATCH', 'PUT'):
            if 'content-length' in request.headers:
                size = int(request.headers['content-length'])
                if size > self.max_size:
                    return Response(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content=json.dumps({'detail': '파일의 크기가 너무 큽니다.'}),
                        media_type='application/json')
        return await call_next(request)