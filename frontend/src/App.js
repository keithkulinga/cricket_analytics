import React, { useState, useEffect } from 'react';
import './App.css';

// This is your clean, exact backend URL on Render
const API_BASE_URL = 'https://cricket-python-backend.onrender.com';

function App() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data from the Python backend
    fetch(`${API_BASE_URL}/api/teams`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setTeams(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching teams:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Cricket Analytics Dashboard</h1>
        
        {/* Show a loading message while waiting for the backend */}
        {loading && <p>Loading Teams...</p>}
        
        {/* Show a helpful red error message if the backend is unreachable */}
        {error && (
          <div style={{ color: '#ff6b6b', background: '#2b0000', padding: '20px', borderRadius: '8px', margin: '20px' }}>
            <h3>Oops! Could not connect to the backend.</h3>
            <p>Error details: {error}</p>
            <p style={{ fontSize: '14px' }}>Check your Render dashboard to make sure the Python backend is "Live".</p>
          </div>
        )}

        {/* Show the grid of teams and logos once data is successfully loaded */}
        {!loading && !error && (
          <div className="team-grid" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '20px' }}>
            {teams.map((team) => (
              <div key={team.id} className="team-card" style={{ background: '#282c34', padding: '20px', borderRadius: '10px', textAlign: 'center', width: '200px' }}>
                <img 
                  src={team.logo_url || 'https://via.placeholder.com/100?text=No+Logo'} 
                  alt={team.name} 
                  className="team-logo"
                  style={{ width: '100px', height: '100px', objectFit: 'contain', marginBottom: '15px' }}
                />
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>{team.name}</h3>
              </div>
            ))}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;