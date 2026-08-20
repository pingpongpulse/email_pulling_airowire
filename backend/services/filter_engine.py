from typing import List
from schemas import RawEmail

class FilterEngine:
    @staticmethod
    def matches_filters(email: RawEmail, keywords: List[str]) -> bool:
        haystack = f"{email.subject} {email.body}".lower()
        return any(kw.lower() in haystack for kw in keywords)
