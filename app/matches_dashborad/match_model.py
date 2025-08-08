from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MatchModel:
    game: str
    status: str
    tournament: str
    tournament_link: str
    tournament_icon: str
    team1: str
    team1_url: str
    logo1_light: str
    logo1_dark: str
    team2: str
    team2_url: str
    logo2_light: str
    logo2_dark: str
    score: str
    match_time: str
    format: str
    stream_links: List[str]
    details_link: str
    match_group: Optional[str]
