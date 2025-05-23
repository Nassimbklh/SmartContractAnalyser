import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ wallet: "", password: "" });
  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:8000/register", form);
      setMessage("✅ Inscription réussie");
      setTimeout(() => navigate("/login"), 1000);
    } catch (err) {
      setMessage("❌ Adresse déjà enregistrée");
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center bg-light vh-100">
      <div className="card shadow-lg p-4 w-100" style={{ maxWidth: "400px" }}>
        <h2 className="text-center mb-4">📝 Inscription</h2>
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
              placeholder="Mot de passe"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>
          <button type="submit" className="btn btn-success w-100">✅ S'inscrire</button>
        </form>
        {message && <div className="alert alert-info mt-3 text-center">{message}</div>}
      </div>
    </div>
  );
}

export default Register;
