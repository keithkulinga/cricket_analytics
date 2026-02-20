import React, { useState, useEffect } from 'react';
import './App.css';

// Make sure this is your actual Render backend URL!
const API_BASE_URL = 'https://cricket-python-backend.onrender.com';

function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 1. Fetching from our brand new live-matches route!
    fetch(`${API_BASE_URL}/api/live-matches`)
      .then(res => {
        if (!res.ok) {
          throw new Error("Failed to fetch matches");
        }
        return res.json();
      })
      .then(data => {
        // The CricketData API puts the match array inside a "data" property
        if (data && data.data) {
          setMatches(data.data);
        } else {
          setMatches([]); 
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching live matches:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Live Cricket Dashboard 🏏</h1>
      </header>
      
      <main style={{ padding: '20px' }}>
        {loading && <h2>Fetching live scores from the cloud...</h2>}
        {error && <h2 style={{ color: 'red' }}>Error: {error}</h2>}
        
        {/* 2. Loop through the matches and create a card for each one */}
        {!loading && !error && (
          <div className="team-grid">
            {matches.length > 0 ? (
              matches.map((match) => (
                <div key={match.id} className="team-card" style={{ padding: '15px', textAlign: 'left' }}>
                  <h3 style={{ marginTop: '0' }}>{match.name}</h3>
                  <p><strong>Status:</strong> {match.status}</p>
                  <p><strong>Venue:</strong> {match.venue}</p>
                  <p><strong>Date:</strong> {new Date(match.date).toLocaleDateString()}</p>
                </div>
              ))
            ) : (
              <p>No live matches found right now.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;