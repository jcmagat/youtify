from dataclasses import dataclass, field

@dataclass
class Track:
    id: str
    image: str
    name: str

@dataclass
class Playlist:
    id: str
    name: str
    description: str
    image: str
    tracks: list[Track] = field(default_factory=list)