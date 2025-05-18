import React, { useState, useContext } from "react";
import axios from "axios";
import { AuthContext } from "./AuthContext";

function Analyze() {
  const [code, setCode] = useState("");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const { token } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("🔄 Envoi du contrat...");

    const formData = new FormData();
    if (file) formData.append("file", file);
    if (code) formData.append("code", code);

    try {
      const res = await axios.post("http://localhost:8000/analyze", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "rapport.md");
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage("✅ Rapport généré !");
    } catch (err) {
      setMessage("❌ Erreur lors de l'analyse");
      console.error(err);
    }
  };

  return (
    <div className="container mt-5">
      <h2>🔍 Analyse de Smart Contract Solidity</h2>
      <form onSubmit={handleSubmit}>
        <label className="form-label mt-3">💻 Coller le code :</label>
        <textarea className="form-control" placeholder={
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Example {\n    uint256 public value;\n\n    function setValue(uint256 _value) public {\n        value = _value;\n    }\n}"
        } rows="10" value={code} onChange={(e) => setCode(e.target.value)}></textarea>

        <div className="text-center my-3">— ou —</div>

        <label className="form-label">📁 Fichier .sol :</label>
        <input type="file" accept=".sol" className="form-control" onChange={(e) => setFile(e.target.files[0])} />

        <button type="submit" className="btn btn-primary mt-3">🚀 Lancer l'analyse</button>
      </form>

      {message && <div className="alert alert-info mt-3">{message}</div>}
    </div>
  );
}

export default Analyze;
