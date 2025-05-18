import React, { useEffect, useState, useContext } from "react";
import axios from "axios";
import { AuthContext } from "./AuthContext";

function History() {
  const { token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:8000/history", {
      headers: { Authorization: `Bearer ${token}` },
    }).then(res => setHistory(res.data)).catch(() => setHistory([]));
  }, [token]);

  return (
    <div className="container mt-5">
      <h2>📜 Historique d’analyse</h2>
      <ul className="list-group mt-4">
        {history.length === 0 && <li className="list-group-item">Aucune analyse encore.</li>}
        {history.map((item, index) => (
          <li key={index} className="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <strong>{item.filename}</strong><br />
              <small className="text-muted">{item.date}</small>
            </div>
            <span className={`badge ${item.status === "OK" ? "bg-success" : "bg-danger"}`}>
              {item.status === "OK" ? "✅ OK" : `❌ ${item.attack}`}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default History;
