from datetime import datetime
import json
from .database import db

class Mailbox(db.Model):
    __tablename__ = 'mailboxes'
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(255), unique=True, nullable=False)
    last_synced_time = db.Column(db.DateTime, default=datetime.min)
    is_active = db.Column(db.Boolean, default=True)

class KeywordFilter(db.Model):
    __tablename__ = 'keyword_filters'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), unique=True, nullable=False)

class EmailThread(db.Model):
    __tablename__ = 'email_threads'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(255), index=True, nullable=True)
    subject = db.Column(db.String(500), nullable=False)
    normalized_subject = db.Column(db.String(500), nullable=True)
    participant_fingerprint = db.Column(db.Text, nullable=True) # Stored as JSON
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    emails = db.relationship('Email', backref='thread', lazy=True)

    def set_fingerprint(self, fingerprint_set):
        self.participant_fingerprint = json.dumps(list(fingerprint_set))
        
    def get_fingerprint(self):
        if not self.participant_fingerprint:
            return frozenset()
        return frozenset(json.loads(self.participant_fingerprint))

class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('email_threads.id'), nullable=False)
    sender = db.Column(db.String(255), nullable=False)
    to_recipients = db.Column(db.Text, nullable=False) # JSON
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=True)
    received_date = db.Column(db.DateTime, nullable=False)
    has_attachments = db.Column(db.Boolean, default=False)
    
    thread_match_confidence = db.Column(db.String(50), default='exact')
    needs_review = db.Column(db.Boolean, default=False)
    
    attachments = db.relationship('Attachment', backref='email', lazy=True)

class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
