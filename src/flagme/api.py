from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="flagme", version="0.0.1")


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


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/flags")
def list_flags() -> list[Flag]:
    return list(_store.values())


@app.get("/flags/{key}")
def get_flag(key: str) -> Flag:
    flag = _store.get(key)
    if flag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown flag: {key}")
    return flag


@app.put("/flags/{key}")
def upsert_flag(key: str, flag: Flag) -> Flag:
    if flag.key != key:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "key in path and body must match"
        )
    _store[key] = flag
    return flag


@app.delete("/flags/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flag(key: str) -> None:
    if _store.pop(key, None) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown flag: {key}")


@app.post("/evaluate/{key}")
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
