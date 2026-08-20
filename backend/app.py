from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from models.database import db
from models.models import Mailbox, KeywordFilter, EmailThread, Email
from scheduler.email_fetch_job import fetch_emails_job
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///airowire.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def setup_initial_data():
    with app.app_context():
        db.create_all()
        # Add default mailbox if empty
        if Mailbox.query.count() == 0:
            default_mb = Mailbox(email_address='invoices@airowire.com')
            db.session.add(default_mb)
        
        # Add default keyword if empty
        if KeywordFilter.query.count() == 0:
            db.session.add(KeywordFilter(keyword='invoice'))
            db.session.add(KeywordFilter(keyword='bill'))
            
        db.session.commit()

setup_initial_data()

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_emails_job, args=[app], trigger="interval", seconds=60)
scheduler.start()

# Stop scheduler when exiting
import atexit
atexit.register(lambda: scheduler.shutdown())

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Airowire Backend API is running. Access the frontend at http://localhost:5173"})

@app.route('/api/threads', methods=['GET'])
def get_threads():
    threads = EmailThread.query.order_by(EmailThread.last_activity.desc()).all()
    result = []
    for t in threads:
        emails = Email.query.filter_by(thread_id=t.id).order_by(Email.received_date.desc()).all()
        needs_review = any(e.needs_review for e in emails)
        result.append({
            'id': t.id,
            'subject': t.subject,
            'last_activity': t.last_activity.isoformat(),
            'email_count': len(emails),
            'needs_review': needs_review
        })
    return jsonify(result)

@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    thread = EmailThread.query.get_or_404(thread_id)
    emails = Email.query.filter_by(thread_id=thread.id).order_by(Email.received_date.asc()).all()
    
    email_list = []
    for e in emails:
        email_list.append({
            'id': e.id,
            'sender': e.sender,
            'date': e.received_date.isoformat(),
            'body': e.body,
            'needs_review': e.needs_review,
            'confidence': e.thread_match_confidence
        })
        
    return jsonify({
        'id': thread.id,
        'subject': thread.subject,
        'emails': email_list
    })

@app.route('/api/send-email', methods=['POST'])
def send_email():
    data = request.json
    # In a real app, we would use the GraphMailSource here.
    # For now, we mock the sending logic.
    print(f"MOCK SENDING EMAIL TO: {data.get('to')} SUBJECT: {data.get('subject')}")
    return jsonify({"success": True, "message": "Email sent successfully (Mocked)"})

if __name__ == '__main__':
    # Run fetch job once on startup
    fetch_emails_job(app)
    app.run(debug=True, use_reloader=False)
