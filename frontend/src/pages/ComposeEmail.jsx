import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function ComposeEmail() {
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [status, setStatus] = useState(null);
  const navigate = useNavigate();

  const handleSend = (e) => {
    e.preventDefault();
    setStatus('sending');
    
    axios.post('http://127.0.0.1:5000/api/send-email', { to, subject, body })
      .then(res => {
        setStatus('success');
        setTimeout(() => navigate('/sent'), 2000);
      })
      .catch(err => {
        console.error("Error sending email:", err);
        setStatus('error');
      });
  };

  return (
    <div>
      <h1 className="page-title">Compose Email</h1>
      
      <div className="card">
        <div className="card-body">
          {status === 'success' && (
            <div style={{ padding: '1rem', backgroundColor: '#d4edda', color: '#155724', borderRadius: '4px', marginBottom: '1rem' }}>
              Email sent successfully (Mocked). Redirecting...
            </div>
          )}
          {status === 'error' && (
            <div style={{ padding: '1rem', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
              Error sending email.
            </div>
          )}
          
          <form onSubmit={handleSend}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>To:</label>
              <input 
                type="email" 
                value={to} 
                onChange={(e) => setTo(e.target.value)} 
                required 
                style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                placeholder="recipient@example.com"
              />
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Subject:</label>
              <input 
                type="text" 
                value={subject} 
                onChange={(e) => setSubject(e.target.value)} 
                required 
                style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                placeholder="Invoice #1234"
              />
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Message:</label>
              <textarea 
                value={body} 
                onChange={(e) => setBody(e.target.value)} 
                required 
                style={{ width: '100%', minHeight: '200px', padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                placeholder="Type your message here..."
              ></textarea>
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={status === 'sending'}
              style={{ width: '100px' }}
            >
              {status === 'sending' ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
