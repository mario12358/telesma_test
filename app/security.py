from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
TRUSTED_FETCH_SITES = frozenset({"same-origin", "none"})


def is_cross_site(request: Request) -> bool:
    """The app has no login or cookies, so a write sent by another site's page is a CSRF attempt."""
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site is not None and fetch_site not in TRUSTED_FETCH_SITES:
        return True
    origin = request.headers.get("origin")
    own_origin = f"{request.url.scheme}://{request.url.netloc}"
    return origin is not None and origin != own_origin


async def reject_cross_site_writes(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if request.method not in SAFE_METHODS and is_cross_site(request):
        return PlainTextResponse("Żądanie z innej witryny zostało odrzucone.", status_code=403)
    return await call_next(request)
