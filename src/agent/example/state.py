from typing import Optional

from typing_extensions import TypedDict


class ExampleState(TypedDict):
    query: str
    context: Optional[list[str]]
