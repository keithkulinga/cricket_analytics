import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, ScatterChart, Scatter
} from 'recharts';
import './App.css';

// --- DEPLOYMENT CONFIG ---
// When you deploy to Render, replace 'your-app-name' with your actual Render URL.
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://cricket-python-backend.onrender.com' // <-- Paste your link here
  : 'http://localhost:5000';

function App() {
  // --- STATE ---
  const [players, setPlayers] = useState([]);
  const [matchStats, setMatchStats] = useState([]);
  const [theme, setTheme] = useState('light');
  const [view, setView] = useState('home'); 
  const [selectedMatch, setSelectedMatch] = useState(null);
  
  const [filterPlayerId, setFilterPlayerId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [compareA, setCompareA] = useState('');
  const [compareB, setCompareB] = useState('');

  const [newPlayer, setNewPlayer] = useState({ first_name: '', last_name: '', role: '', team: '', image_url: '' });
  const [stats, setStats] = useState({ 
    player_id: '', runs: '', balls: '', fours: '', sixes: '', 
    wickets: '', overs: '', runs_conceded: '', 
    catches: '', stumpings: '', run_outs: '',
    match_date: '', opposition: '', venue: '', match_result: 'Won' 
  });

  const THEME_STYLES = {
      light: { bg: "#f0f2f5", card: "white", text: "#1c1e21", nav: "#1877f2", subtext: "#606770" },
      dark: { bg: "#18191a", card: "#242526", text: "#e4e6eb", nav: "#242526", subtext: "#b0b3b8" }
  };
  const currentTheme = THEME_STYLES[theme];

  // --- API CALLS (Using Deployment URL) ---
  useEffect(() => { fetchPlayers(); fetchStats(); }, []);

  const fetchPlayers = async () => { 
    try { 
        const res = await fetch(`${API_BASE_URL}/api/players`);
        setPlayers(await res.json()); 
    } catch (e) { console.error("Error fetching players:", e); } 
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/stats`);
      let data = await res.json();
      data.sort((a, b) => new Date(b.match_date) - new Date(a.match_date));
      setMatchStats(data);
    } catch (e) { console.error("Error fetching stats:", e); }
  };

  const handleAddPlayer = async (e) => {
    e.preventDefault();
    await fetch(`${API_BASE_URL}/api/players`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(newPlayer) 
    });
    setNewPlayer({ first_name: '', last_name: '', role: '', team: '', image_url: '' });
    fetchPlayers();
  };

  const handleAddStats = async (e) => {
    e.preventDefault();
    const payload = { ...stats, match_date: stats.match_date || new Date().toISOString().split('T')[0] };
    const res = await fetch(`${API_BASE_URL}/api/stats`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify(payload) 
    });
    if (res.ok) {
      alert("Stats Recorded!");
      setStats({ player_id: '', runs: '', balls: '', fours: '', sixes: '', wickets: '', overs: '', runs_conceded: '', catches: '', stumpings: '', run_outs: '', match_date: '', opposition: '', venue: '', match_result: 'Won' });
      fetchStats();
    }
  };

  // --- ANALYTICS LOGIC ---
  const getPlayerStats = (pid) => {
    if (!pid) return null;
    const p = players.find(p => p.id === parseInt(pid));
    if (!p) return null;
    const pStats = matchStats.filter(s => s.player_id === parseInt(pid));
    
    const runs = pStats.reduce((acc, curr) => acc + curr.runs, 0);
    const balls = pStats.reduce((acc, curr) => acc + curr.balls, 0);
    const fours = pStats.reduce((acc, curr) => acc + curr.fours, 0);
    const sixes = pStats.reduce((acc, curr) => acc + curr.sixes, 0);
    const wickets = pStats.reduce((acc, curr) => acc + (curr.wickets || 0), 0);
    const overs = pStats.reduce((acc, curr) => acc + (curr.overs || 0), 0);
    const runsConceded = pStats.reduce((acc, curr) => acc + (curr.runs_conceded || 0), 0);
    
    const scoringData = [
        { name: 'Sixes', value: sixes * 6, fill: '#e74c3c' },
        { name: 'Fours', value: fours * 4, fill: '#f1c40f' },
        { name: 'Others', value: Math.max(0, runs - (sixes * 6 + fours * 4)), fill: '#3498db' }
    ];

    return { 
        ...p, runs, wickets, 
        avg: pStats.length > 0 ? (runs / pStats.length).toFixed(1) : 0,
        sr: balls > 0 ? ((runs / balls) * 100).toFixed(1) : 0,
        economy: overs > 0 ? (runsConceded / overs).toFixed(2) : 0,
        mvpScore: (runs * 1) + (wickets * 20) + (pStats.reduce((a,c)=>a+c.catches,0)*10),
        scoringData,
        trendData: [...pStats].sort((a,b) => new Date(a.match_date) - new Date(b.match_date))
    };
  };

  const allPlayerStats = players.map(p => getPlayerStats(p.id)).filter(p => p !== null);

  const getLeaders = () => {
    if(allPlayerStats.length === 0) return {};
    return {
        orange: [...allPlayerStats].sort((a,b) => b.runs - a.runs)[0],
        purple: [...allPlayerStats].sort((a,b) => b.wickets - a.wickets)[0],
    };
  };
  const leaders = getLeaders();

  // --- STYLES ---
  const pageStyle = { padding: "20px", fontFamily: "'Segoe UI', Roboto, sans-serif", maxWidth: "1200px", margin: "0 auto", backgroundColor: currentTheme.bg, color: currentTheme.text, minHeight: "100vh" };
  const cardStyle = { background: currentTheme.card, padding: "20px", borderRadius: "12px", boxShadow: "0 2px 4px rgba(0,0,0,0.1)" };
  const navBtn = { padding: "10px 20px", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "600", transition: "0.2s" };

  return (
    <div style={pageStyle}>
      {/* HEADER & NAV */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "25px", background: currentTheme.nav, padding: "15px 25px", borderRadius: "15px", color: "white" }}>
        <h2 style={{ margin: 0 }}>📊 CRIC-ANALYTICS</h2>
        <div style={{display: "flex", gap: "10px"}}>
          {['home', 'profile', 'compare'].map(v => (
            <button key={v} onClick={() => setView(v)} style={{ ...navBtn, background: view === v ? '#fff' : 'transparent', color: view === v ? '#1877f2' : '#fff' }}>{v.toUpperCase()}</button>
          ))}
          <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} style={{background:"rgba(255,255,255,0.2)", border:"none", borderRadius:"8px", padding:"0 15px", color:"white", cursor:"pointer"}}>{theme==='light'?'🌙':'☀️'}</button>
        </div>
      </div>

      {/* DASHBOARD VIEW */}
      {view === 'home' && (
        <div style={{display: "flex", flexDirection: "column", gap: "25px"}}>
            <div style={{display: "flex", gap: "20px", flexWrap: "wrap"}}>
                {leaders.orange && <LeaderCard title="Orange Cap" player={leaders.orange} val={leaders.orange.runs} unit="Runs" color="#f39c12" />}
                {leaders.purple && <LeaderCard title="Purple Cap" player={leaders.purple} val={leaders.purple.wickets} unit="Wickets" color="#9b59b6" />}
            </div>

            <div style={{...cardStyle, height: "400px"}}>
                <h3>🎯 Impact Matrix (Runs vs Wickets)</h3>
                <ResponsiveContainer width="100%" height="90%">
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" dataKey="runs" name="Runs" label={{ value: 'Total Runs', position: 'insideBottom', offset: -5 }} />
                        <YAxis type="number" dataKey="wickets" name="Wickets" label={{ value: 'Total Wickets', angle: -90, position: 'insideLeft' }} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                        <Scatter name="Players" data={allPlayerStats} fill="#1877f2">
                            {allPlayerStats.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.runs > 100 ? '#e74c3c' : '#1877f2'} />
                            ))}
                        </Scatter>
                    </ScatterChart>
                </ResponsiveContainer>
            </div>
        </div>
      )}

      {/* PROFILE VIEW */}
      {view === 'profile' && (
        <div style={{display: "flex", flexDirection: "column", gap: "20px"}}>
            <select value={filterPlayerId} onChange={(e) => setFilterPlayerId(e.target.value)} style={{padding: "12px", borderRadius: "8px", border: "1px solid #ddd", width: "100%", maxWidth: "400px"}}>
                <option value="">Search Player Profile...</option>
                {players.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}
            </select>

            {getPlayerStats(filterPlayerId) && (
                <div style={{display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px"}}>
                    <div style={cardStyle}>
                        <div style={{textAlign: "center", marginBottom: "20px"}}>
                            <img src={getPlayerStats(filterPlayerId).image_url || 'https://via.placeholder.com/150'} alt="" style={{width: "120px", height: "120px", borderRadius: "50%", border: "4px solid #1877f2", objectFit: "cover"}} />
                            <h2>{getPlayerStats(filterPlayerId).first_name}</h2>
                            <p style={{color: "#777"}}>{getPlayerStats(filterPlayerId).team}</p>
                        </div>
                        <div style={{display: "flex", justifyContent: "space-around", borderTop: "1px solid #eee", paddingTop: "20px"}}>
                            <div><small>AVG</small><div style={{fontSize: "1.2em", fontWeight: "bold"}}>{getPlayerStats(filterPlayerId).avg}</div></div>
                            <div><small>SR</small><div style={{fontSize: "1.2em", fontWeight: "bold"}}>{getPlayerStats(filterPlayerId).sr}</div></div>
                            <div><small>WKT</small><div style={{fontSize: "1.2em", fontWeight: "bold"}}>{getPlayerStats(filterPlayerId).wickets}</div></div>
                        </div>
                    </div>
                    
                    <div style={cardStyle}>
                        <h3>Boundary Breakdown</h3>
                        <div style={{height: "200px"}}>
                            <ResponsiveContainer>
                                <PieChart>
                                    <Pie data={getPlayerStats(filterPlayerId).scoringData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                                        {getPlayerStats(filterPlayerId).scoringData.map((entry, index) => <Cell key={index} fill={entry.fill} />)}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div style={{display: "flex", justifyContent: "center", gap: "15px", fontSize: "0.8em"}}>
                            <span style={{color: "#e74c3c"}}>● 6s</span> <span style={{color: "#f1c40f"}}>● 4s</span> <span style={{color: "#3498db"}}>● Others</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
      )}

      {/* FOOTER / ADMIN INFO */}
      <div style={{marginTop: "50px", opacity: 0.8}}>
          <hr style={{borderColor: "#ddd"}} />
          <p style={{textAlign: "center", color: "#777", fontSize: "0.9em"}}>
            Season Data Dashboard • Mode: {process.env.NODE_ENV}
          </p>
      </div>
    </div>
  );
}

// Reusable LeaderCard Component
const LeaderCard = ({ title, player, val, unit, color }) => (
    <div style={{ flex: 1, minWidth: "250px", background: "white", padding: "20px", borderRadius: "15px", borderBottom: `5px solid ${color}`, display: "flex", alignItems: "center", gap: "15px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
        <img src={player.image_url || 'https://via.placeholder.com/60'} alt="" style={{ width: "60px", height: "60px", borderRadius: "50%", objectFit: "cover" }} />
        <div>
            <div style={{ fontSize: "0.8em", color: "#777", textTransform: "uppercase" }}>{title}</div>
            <div style={{ fontWeight: "bold", fontSize: "1.1em" }}>{player.first_name} {player.last_name}</div>
            <div style={{ color: color, fontWeight: "800", fontSize: "1.4em" }}>{val} <small style={{fontSize: "0.5em"}}>{unit}</small></div>
        </div>
    </div>
);

export default App;