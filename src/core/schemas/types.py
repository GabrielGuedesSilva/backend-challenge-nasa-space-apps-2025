from typing import Annotated

from pydantic import Field, StringConstraints

NonEmptyStr = Annotated[
    str, StringConstraints(min_length=1, strip_whitespace=True)
]
NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0)]
UserName = Annotated[
    str, StringConstraints(min_length=5, strip_whitespace=True)
]
