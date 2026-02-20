import React, { useState, useEffect } from 'react';
import './App.css';

// REPLACE THIS with your actual Render backend URL
const API_BASE_URL = 'https://cricket-python-backend-xxxx.onrender.com'; 

function App() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/teams`)
      .then(res => res.json())
      .then(data => {
        setTeams(data);
        setLoading(false);
      })
      .catch(err => console.error("Error fetching teams:", err));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Cricket Analytics Dashboard</h1>
        {loading ? <p>Loading Teams...</p> : (
          <div className="team-grid">
            {teams.map(team => (
              <div key={team.id} className="team-card">
                <img src={team.logo_url} alt={team.name} className="team-logo" />
                <h3>{team.name}</h3>
              </div>
            ))}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;