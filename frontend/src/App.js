import React, { useState, useEffect } from 'react';
import './App.css';

// Make sure this is your actual Render backend URL!
const API_BASE_URL = 'https://cricket-python-backend.onrender.com';

function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 1. We wrap our fetch logic inside a function so we can reuse it
    const fetchMatches = () => {
      fetch(`${API_BASE_URL}/api/live-matches`)
        .then(res => {
          if (!res.ok) {
            throw new Error("Failed to fetch matches");
          }
          return res.json();
        })
        .then(data => {
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
    };

    // 2. Fetch the matches immediately when the page first loads
    fetchMatches();

    // 3. Set up a timer to run fetchMatches again every 30 seconds (30000 milliseconds)
    const intervalId = setInterval(fetchMatches, 30000);

    // 4. This cleanup function stops the timer if the user closes the dashboard
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Live Cricket Dashboard 🏏</h1>
      </header>
      
      <main style={{ padding: '20px' }}>
        {loading && <h2>Fetching live scores from the cloud...</h2>}
        {error && <h2 style={{ color: 'red' }}>Error: {error}</h2>}
        
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