import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'https://cricket-python-backend.onrender.com';

function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [showOnlyLive, setShowOnlyLive] = useState(false);
  // NEW: State to store what the user types in the search bar
  const [searchQuery, setSearchQuery] = useState("");

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

  // NEW: Double-filter! Check if the match passes the "Live" filter AND the "Search" filter
  const displayedMatches = matches.filter(match => {
    const passesLiveFilter = showOnlyLive ? !match.status.toLowerCase().includes("won") : true;
    const passesSearchFilter = match.name.toLowerCase().includes(searchQuery.toLowerCase());
    
    return passesLiveFilter && passesSearchFilter;
  });

  return (
    <div className="App">
      <header className="App-header">
        <h1>Live Cricket Dashboard 🏏</h1>
        
        {/* NEW: A container to hold our search bar and filter button side-by-side */}
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
        {loading && <h2>Fetching live scores from the cloud...</h2>}
        {error && <h2 style={{ color: 'red' }}>Error: {error}</h2>}
        
        {!loading && !error && (
          <div className="team-grid">
            {displayedMatches.length > 0 ? (
              displayedMatches.map((match) => (
                <div key={match.id} className="team-card" style={{ padding: '15px', textAlign: 'left' }}>
                  <h3 style={{ marginTop: '0' }}>{match.name}</h3>
                  <p><strong>Status:</strong> {match.status}</p>
                  <p><strong>Venue:</strong> {match.venue}</p>
                  <p><strong>Date:</strong> {new Date(match.date).toLocaleDateString()}</p>
                </div>
              ))
            ) : (
              <p>No matches found matching "{searchQuery}" right now.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;