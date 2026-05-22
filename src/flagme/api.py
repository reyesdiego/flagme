from typing import Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from flagme import __version__

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


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


class Flag(BaseModel):
    key: str = Field(min_length=1)
    enabled: bool = False
    description: str = ""


class EvaluationContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    subject: str | None = None


class Evaluation(BaseModel):
    key: str
    value: bool
    reason: Literal["FLAG_ENABLED", "FLAG_DISABLED"]


_store: dict[str, Flag] = {}


@app.get("/healthz", tags=["System"], summary="Liveness probe")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/flags", tags=["Flags"], summary="List all flags")
def list_flags() -> list[Flag]:
    return list(_store.values())


@app.get("/flags/{key}", tags=["Flags"], summary="Get a flag by key")
def get_flag(key: str) -> Flag:
    flag = _store.get(key)
    if flag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown flag: {key}")
    return flag


@app.put("/flags/{key}", tags=["Flags"], summary="Create or replace a flag")
def upsert_flag(key: str, flag: Flag) -> Flag:
    if flag.key != key:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "key in path and body must match"
        )
    _store[key] = flag
    return flag


@app.delete(
    "/flags/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Flags"],
    summary="Delete a flag",
)
def delete_flag(key: str) -> None:
    if _store.pop(key, None) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown flag: {key}")


@app.post("/evaluate/{key}", tags=["Evaluation"], summary="Evaluate a flag")
def evaluate(key: str, context: EvaluationContext | None = None) -> Evaluation:
    del context  # unused until rules/targeting land; accepted to shape the API
    flag = _store.get(key)
    if flag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown flag: {key}")
    return Evaluation(
        key=key,
        value=flag.enabled,
        reason="FLAG_ENABLED" if flag.enabled else "FLAG_DISABLED",
    )
