from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from flagme import __version__
from flagme.models import (
    Evaluation,
    EvaluationContext,
    Flag,
    FlagInput,
)
from flagme.storage import (
    FlagNotFound,
    FlagStorage,
    default_db_path,
    evaluate_value,
)

_OPENAPI_TAGS = [
    {"name": "System", "description": "Liveness and service metadata."},
    {"name": "Flags", "description": "Manage feature flag definitions."},
    {"name": "Evaluation", "description": "Resolve a flag's value for a given context."},
]

app = FastAPI(
    title="flagme",
    version=__version__,
    description=(
        "Feature flag service. Interactive docs at `/docs` and `/redoc`; "
        "machine-readable OpenAPI spec at `/openapi.json`."
    ),
    openapi_tags=_OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_storage: FlagStorage | None = None


def get_storage() -> FlagStorage:
    global _storage
    if _storage is None:
        _storage = FlagStorage(default_db_path())
    return _storage


StorageDep = Annotated[FlagStorage, Depends(get_storage)]


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/healthz", tags=["System"], summary="Liveness probe")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/flags", tags=["Flags"], summary="List flags")
def list_flags(
    storage: StorageDep,
    environment: str | None = None,
    user_id: str | None = None,
) -> list[Flag]:
    return storage.list_flags(environment=environment, user_id=user_id)


@app.get("/flags/{flag_id}", tags=["Flags"], summary="Get a flag by id")
def get_flag(flag_id: UUID, storage: StorageDep) -> Flag:
    try:
        return storage.get(flag_id)
    except FlagNotFound:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"unknown flag id: {flag_id}"
        ) from None


@app.post(
    "/flags",
    tags=["Flags"],
    summary="Create a flag",
    status_code=status.HTTP_201_CREATED,
)
def create_flag(payload: FlagInput, storage: StorageDep) -> Flag:
    flag = Flag.model_validate(payload.model_dump())
    return storage.create(flag)


@app.put("/flags/{flag_id}", tags=["Flags"], summary="Replace a flag")
def update_flag(flag_id: UUID, payload: FlagInput, storage: StorageDep) -> Flag:
    flag = Flag.model_validate({**payload.model_dump(), "id": flag_id})
    try:
        return storage.update(flag)
    except FlagNotFound:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"unknown flag id: {flag_id}"
        ) from None


@app.delete(
    "/flags/{flag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Flags"],
    summary="Delete a flag",
)
def delete_flag(flag_id: UUID, storage: StorageDep) -> None:
    try:
        storage.delete(flag_id)
    except FlagNotFound:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"unknown flag id: {flag_id}"
        ) from None


@app.post("/evaluate/{key}", tags=["Evaluation"], summary="Evaluate a flag")
def evaluate(
    key: str,
    storage: StorageDep,
    context: EvaluationContext | None = None,
) -> Evaluation:
    ctx = context or EvaluationContext()
    flag = storage.find_match(
        key,
        environment=ctx.environment,
        user_id=ctx.user_id,
        now=datetime.now(timezone.utc),
    )
    if flag is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"no matching flag for key: {key}"
        )
    return Evaluation(
        key=key,
        value_type=flag.value_type,
        value=evaluate_value(flag),
        matched_flag_id=flag.id,
    )
