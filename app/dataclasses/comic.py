from typing import List
from dataclasses import dataclass

@dataclass
class Comic_Issue:
    title: str 
    url: str

@dataclass
class Comic_Images:
    issue: Comic_Issue
    image_urls: List[str]