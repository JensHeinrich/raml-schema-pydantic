from datetime import date
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import validator


class A(BaseModel):
    name: str
    age: int
    birthdate: date

    @validator("birthdate")
    def _convert_string_to_date(cls, v: Any) -> date:
        return date.fromisoformat(v)

    def do_something(self) -> str:
        return "something"


class B(A):
    age: str
    birthdate: date | None = None

    def do_something(self) -> Literal["something entirely different"]:
        return "something entirely different"


b = B(name="B.", age="f")

r = b.do_something()
