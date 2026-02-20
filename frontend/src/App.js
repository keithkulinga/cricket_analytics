import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'https://cricket-python-backend.onrender.com';

function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showOnlyLive, setShowOnlyLive] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  useEffect(() => {
    const fetchMatches = () => {
      fetch(`${API_BASE_URL}/api/live-matches`)
        .then(res => {
          if (!res.ok) throw new Error("Failed to fetch matches");
          return res.json();
        })
        .then(data => {
          if (data && data.data) {
            setMatches(data.data);
          } else {
            setMatches([]); 
          }
          setLoading(false);
          setLastUpdated(new Date().toLocaleTimeString());
        })
        .catch(err => {
          console.error("Error fetching live matches:", err);
          setError(err.message);
          setLoading(false);
        });
    };

    fetchMatches();
    const intervalId = setInterval(fetchMatches, 30000);
    return () => clearInterval(intervalId);
  }, []);

  const displayedMatches = matches.filter(match => {
    const passesLiveFilter = showOnlyLive ? !match.status.toLowerCase().includes("won") : true;
    const passesSearchFilter = match.name.toLowerCase().includes(searchQuery.toLowerCase());
    return passesLiveFilter && passesSearchFilter;
  });

  // NEW: Sort matches so that "Live" matches appear at the top!
  const sortedMatches = [...displayedMatches].sort((a, b) => {
    const aIsFinished = a.status.toLowerCase().includes("won");
    const bIsFinished = b.status.toLowerCase().includes("won");
    
    // If 'a' is live (not finished) and 'b' is finished, 'a' goes first
    if (!aIsFinished && bIsFinished) return -1;
    // If 'a' is finished and 'b' is live, 'b' goes first
    if (aIsFinished && !bIsFinished) return 1;
    // Otherwise, leave them in the order they came in
    return 0;
  });

  return (
    <div className="App">
      <header className="App-header">
        <h1>Live Cricket Dashboard 🏏</h1>
        
        {lastUpdated && <p className="last-updated-text">🟢 Live updates • Last checked: {lastUpdated}</p>}

        <div className="controls-container">
          <input 
            type="text" 
            className="search-bar" 
            placeholder="Search for a team or match..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button 
            className="filter-button"
            onClick={() => setShowOnlyLive(!showOnlyLive)}
          >
            {showOnlyLive ? "Show All Matches" : "🔴 Show Live Only"}
          </button>
        </div>
      </header>
      
      <main style={{ padding: '20px' }}>
        {loading && <div className="spinner"></div>}
        {error && <h2 style={{ color: 'red' }}>Error: {error}</h2>}
        
        {!loading && !error && (
          <div className="team-grid">
            {/* NEW: We are now displaying sortedMatches instead of displayedMatches */}
            {sortedMatches.length > 0 ? (
              sortedMatches.map((match) => (
                <div key={match.id} className="team-card" style={{ padding: '15px', textAlign: 'left' }}>
                  <h3 style={{ marginTop: '0' }}>{match.name}</h3>
                  <p><strong>Status:</strong> {match.status}</p>
                  <p><strong>Venue:</strong> {match.venue}</p>
                  <p><strong>Date:</strong> {new Date(match.date).toLocaleDateString()}</p>
                </div>
              ))
            ) : (
              <p>No matches found right now.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;