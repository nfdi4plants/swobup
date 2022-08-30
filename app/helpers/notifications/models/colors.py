from typing import Optional, Dict, List

from pydantic import BaseModel, validator

from app.github.models.user import User
from app.github.models.author import Author


class Warning(BaseModel):
    primary_color: str = "#c21f3a"
    secondary_color: str = "#F2D2D7"
    font_color: str = "#871528"


class Success(BaseModel):
    primary_color: str = "#d2f3ed"
    secondary_color: str = "#168875"
    font_color: str = "#168875"

class Colors(BaseModel):
    headline: str = "#ffc000"
    line_color_blue: str = "#4caed3"
    line_color_yellow: str = "#ffc000"