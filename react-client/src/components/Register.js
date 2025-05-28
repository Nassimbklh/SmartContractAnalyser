import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../services/api";
import { handleApiError } from "../utils/utils";

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ wallet: "", password: "" });
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info"); // info / success / danger

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // 🔎 Vérifications côté front
    if (!form.wallet.startsWith("0x") || form.wallet.length !== 42) {
      setMessage("❌ L'adresse doit être un wallet Ethereum valide (0x...)");
      setMessageType("danger");
      return;
    }
    if (form.password.length < 8) {
      setMessage("❌ Le mot de passe doit contenir au moins 8 caractères");
      setMessageType("danger");
      return;
    }

    try {
      await authAPI.register(form);
      setMessage("✅ Inscription réussie !");
      setMessageType("success");
      setTimeout(() => navigate("/login"), 1500);
    } catch (error) {
      const errorMessage = handleApiError(error) || "❌ Erreur lors de l'inscription";
      setMessage(errorMessage);
      setMessageType("danger");
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
              placeholder="Mot de passe (min. 8 caractères)"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>
          <button type="submit" className="btn btn-success w-100">✅ S'inscrire</button>
        </form>
        {message && (
          <div className={`alert alert-${messageType} mt-3 text-center`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

export default Register;
