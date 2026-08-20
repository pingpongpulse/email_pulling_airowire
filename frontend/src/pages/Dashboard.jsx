import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';

export default function Dashboard() {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // In dev, assuming proxy is setup or running on localhost:5000
    axios.get('http://127.0.0.1:5000/api/threads')
      .then(res => {
        setThreads(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching threads:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading threads...</div>;

  return (
    <div>
      <h1 className="page-title">Invoice Threads</h1>
      
      <div className="card">
        <div className="card-header">
          <h3>Recent Conversations</h3>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {threads.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No invoice threads found yet. Is the background fetch job running?
            </div>
          ) : (
            threads.map(thread => (
              <div 
                key={thread.id} 
                className="thread-item"
                onClick={() => navigate(`/thread/${thread.id}`)}
              >
                <div>
                  <div className="thread-subject">{thread.subject}</div>
                  <div className="thread-meta">
                    {new Date(thread.last_activity).toLocaleString()} • {thread.email_count} emails
                  </div>
                </div>
                {thread.needs_review && (
                  <div className="badge badge-warning" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <AlertCircle size={14} />
                    Needs Review
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
