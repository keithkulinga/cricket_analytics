import React, { useState, useEffect } from 'react';
/* NEW: Import the chart components from recharts */
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

const API_BASE_URL = 'https://cricket-python-backend.onrender.com';

/* NEW: Mock Data for our Analytics Chart */
const mockAnalyticsData = [
  { name: 'India', wins: 45, losses: 12 },
  { name: 'Australia', wins: 42, losses: 15 },
  { name: 'England', wins: 38, losses: 20 },
  { name: 'Pakistan', wins: 35, losses: 22 },
  { name: 'South Africa', wins: 30, losses: 25 },
];

function App() {
  const [activeTab, setActiveTab] = useState("live");

  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showOnlyLive, setShowOnlyLive] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const [teams, setTeams] = useState([]);
  const [loadingTeams, setLoadingTeams] = useState(false);

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

  useEffect(() => {
    if (activeTab === "teams" && teams.length === 0) {
      setLoadingTeams(true);
      fetch(`${API_BASE_URL}/api/teams`)
        .then(res => res.json())
        .then(data => {
          const teamsData = data.teams || data || [];
          setTeams(teamsData);
          setLoadingTeams(false);
        })
        .catch(err => {
          console.error("Error fetching teams:", err);
          setLoadingTeams(false);
        });
    }
  }, [activeTab, teams.length]);

  const displayedMatches = matches.filter(match => {
    const passesLiveFilter = showOnlyLive ? !match.status.toLowerCase().includes("won") : true;
    const passesSearchFilter = match.name.toLowerCase().includes(searchQuery.toLowerCase());
    return passesLiveFilter && passesSearchFilter;
  });

  const sortedMatches = [...displayedMatches].sort((a, b) => {
    const aIsFinished = a.status.toLowerCase().includes("won");
    const bIsFinished = b.status.toLowerCase().includes("won");
    if (!aIsFinished && bIsFinished) return -1;
    if (aIsFinished && !bIsFinished) return 1;
    return 0;
  });

  return (
    <div className="App">
      
      <nav className="top-nav">
        <button className={activeTab === "live" ? "nav-btn active" : "nav-btn"} onClick={() => setActiveTab("live")}>
          🏏 Live Matches
        </button>
        <button className={activeTab === "teams" ? "nav-btn active" : "nav-btn"} onClick={() => setActiveTab("teams")}>
          🛡️ Team List
        </button>
        <button className={activeTab === "analytics" ? "nav-btn active" : "nav-btn"} onClick={() => setActiveTab("analytics")}>
          📊 Analytics
        </button>
      </nav>

      {/* --- LIVE MATCHES TAB --- */}
      {activeTab === "live" && (
        <>
          <header className="App-header">
            <h1>Live Cricket Dashboard</h1>
            {lastUpdated && <p className="last-updated-text">🟢 Live updates • Last checked: {lastUpdated}</p>}

            <div className="controls-container">
              <input 
                type="text" 
                className="search-bar" 
                placeholder="Search for a team or match..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button className="filter-button" onClick={() => setShowOnlyLive(!showOnlyLive)}>
                {showOnlyLive ? "Show All Matches" : "🔴 Show Live Only"}
              </button>
            </div>
          </header>
          
          <main style={{ padding: '20px' }}>
            {loading && <div className="spinner"></div>}
            {error && <h2 style={{ color: 'red' }}>Error: {error}</h2>}
            {!loading && !error && (
              <div className="team-grid">
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
        </>
      )}

      {/* --- TEAMS TAB --- */}
      {activeTab === "teams" && (
        <div style={{ padding: '20px' }}>
          <header className="App-header">
            <h1>🛡️ Teams Database</h1>
          </header>
          <main>
            {loadingTeams ? (
              <div className="spinner"></div>
            ) : (
              <div className="team-grid">
                {teams.length > 0 ? (
                  teams.map((team, index) => (
                    <div key={index} className="team-card" style={{ padding: '15px', textAlign: 'left' }}>
                      <h3 style={{ marginTop: '0', color: '#00ff88' }}>{team.name || "Unknown Team"}</h3>
                      <p><strong>City/Country:</strong> {team.city || team.country || "N/A"}</p>
                    </div>
                  ))
                ) : (
                  <p style={{ color: 'white' }}>No teams found in the database.</p>
                )}
              </div>
            )}
          </main>
        </div>
      )}

      {/* --- ANALYTICS TAB --- */}
      {activeTab === "analytics" && (
        <div style={{ padding: '20px', color: 'white' }}>
           <header className="App-header">
            <h1>📊 Team Analytics</h1>
          </header>
          
          {/* NEW: The Interactive Chart Container */}
          <main style={{ maxWidth: '900px', margin: '0 auto', backgroundColor: '#242424', padding: '30px', borderRadius: '15px', boxShadow: '0 4px 6px rgba(0,0,0,0.3)' }}>
            <h2 style={{ marginTop: '0', marginBottom: '30px', color: '#00ff88' }}>Win/Loss Record (Top Teams)</h2>
            
            <div style={{ width: '100%', height: 400 }}>
              <ResponsiveContainer>
                <BarChart data={mockAnalyticsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="name" stroke="#ccc" />
                  <YAxis stroke="#ccc" />
                  {/* Tooltip makes a cool pop-up box appear when you hover over the bars! */}
                  <Tooltip contentStyle={{ backgroundColor: '#121212', borderColor: '#333', color: '#fff' }} />
                  <Legend wrapperStyle={{ paddingTop: '20px' }}/>
                  <Bar dataKey="wins" fill="#00ff88" name="Wins" radius={[5, 5, 0, 0]} />
                  <Bar dataKey="losses" fill="#ff4d4d" name="Losses" radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </main>
        </div>
      )}

    </div>
  );
}

export default App;