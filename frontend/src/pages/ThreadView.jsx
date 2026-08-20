import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle } from 'lucide-react';

export default function ThreadView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [thread, setThread] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`http://127.0.0.1:5000/api/threads/${id}`)
      .then(res => {
        setThread(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching thread:", err);
        setLoading(false);
      });
  }, [id]);

  if (loading) return <div>Loading thread...</div>;
  if (!thread) return <div>Thread not found.</div>;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem', gap: '1rem' }}>
        <button className="btn" onClick={() => navigate(-1)} style={{ backgroundColor: 'var(--border-color)' }}>
          <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} /> Back
        </button>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{thread.subject}</h1>
      </div>

      {thread.emails.map((email, idx) => (
        <div key={email.id} className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header" style={{ backgroundColor: email.needs_review ? 'var(--warning-bg)' : 'transparent' }}>
            <div>
              <strong>{email.sender}</strong>
              <div className="thread-meta">{new Date(email.date).toLocaleString()}</div>
            </div>
            
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              {email.needs_review && (
                <div style={{ color: 'var(--warning-text)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
                  <AlertTriangle size={16} />
                  Possibly unrelated (Confidence: {email.confidence})
                </div>
              )}
              <div className="badge" style={{ backgroundColor: 'var(--border-color)' }}>
                Match: {email.confidence}
              </div>
            </div>
          </div>
          <div className="card-body">
            <p style={{ whiteSpace: 'pre-wrap' }}>{email.body}</p>
          </div>
        </div>
      ))}
      
      <div className="card">
        <div className="card-body">
          <h4 style={{ marginBottom: '1rem' }}>Reply to thread</h4>
          <textarea 
            style={{ width: '100%', minHeight: '100px', padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: '6px', marginBottom: '1rem' }}
            placeholder="Type your reply here..."
          ></textarea>
          <button className="btn btn-primary">Send Reply</button>
        </div>
      </div>
    </div>
  );
}
