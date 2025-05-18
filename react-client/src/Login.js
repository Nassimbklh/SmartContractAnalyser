import React, { useState, useContext } from "react";
import axios from "axios";
import { AuthContext } from "./AuthContext";
import { useNavigate } from "react-router-dom";

function Login() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [form, setForm] = useState({ wallet: "", password: "" });
  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://localhost:8000/login", form);
      login(res.data.access_token);
      navigate("/analyze");
    } catch {
      setMessage("❌ Adresse ou mot de passe invalide");
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center bg-light vh-100">
      <div className="card shadow-lg p-4 w-100" style={{ maxWidth: "400px" }}>
        <h2 className="text-center mb-4">🔐 Connexion</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">📬 Adresse de portefeuille</label>
            <input
              className="form-control"
              name="wallet"
              placeholder="0x..."
              value={form.wallet}
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <label className="form-label">🔒 Mot de passe</label>
            <input
              type="password"
              className="form-control"
              name="password"
              placeholder="Mot de passe"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary w-100">➡️ Se connecter</button>
        </form>
        {message && <div className="alert alert-danger mt-3 text-center">{message}</div>}
      </div>
    </div>
  );
}

export default Login;
