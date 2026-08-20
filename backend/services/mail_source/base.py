from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from schemas import RawEmail

class SendResult:
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

class MailSourceInterface(ABC):
    @abstractmethod
    def fetch_messages(self, mailbox: str, since: datetime) -> List[RawEmail]:
        pass
    
    @abstractmethod
    def send_message(self, mailbox: str, to: List[str], subject: str, body: str, attachments: List[str]) -> SendResult:
        pass
