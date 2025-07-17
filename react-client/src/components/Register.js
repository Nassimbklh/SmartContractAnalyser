import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../services/api";
import { handleApiError } from "../utils/utils";

// Questions techniques pour l'évaluation
const technicalQuestions = [
  {
    question: "Que fait la fonction fallback() en Solidity ?",
    options: [
      { text: "Elle exécute automatiquement un transfert ETH", isCorrect: false },
      { text: "Elle est appelée quand aucune autre fonction ne correspond", isCorrect: true },
      { text: "Elle initialise le contrat", isCorrect: false },
      { text: "Elle supprime le contrat", isCorrect: false }
    ]
  },
  {
    question: "Quel est le problème principal du pattern call.value() ?",
    options: [
      { text: "Manque de lisibilité", isCorrect: false },
      { text: "Ralentit la transaction", isCorrect: false },
      { text: "Vulnérabilité à la réentrance", isCorrect: true },
      { text: "Pas compatible avec MetaMask", isCorrect: false }
    ]
  },
  {
    question: "Le mot-clé view dans une fonction Solidity signifie que :",
    options: [
      { text: "Elle modifie l'état du contrat", isCorrect: false },
      { text: "Elle ne retourne rien", isCorrect: false },
      { text: "Elle peut seulement lire l'état", isCorrect: true },
      { text: "Elle est privée", isCorrect: false }
    ]
  },
  {
    question: "Que retourne msg.sender dans une fonction appelée via un proxy ?",
    options: [
      { text: "L'adresse du proxy", isCorrect: false },
      { text: "L'adresse du wallet qui initie la transaction", isCorrect: true },
      { text: "Toujours l'adresse 0x0", isCorrect: false },
      { text: "Le compilateur choisit aléatoirement", isCorrect: false }
    ]
  },
  {
    question: "Pourquoi utilise-t-on require() en Solidity ?",
    options: [
      { text: "Pour compiler un contrat", isCorrect: false },
      { text: "Pour conditionner l'exécution d'une fonction", isCorrect: true },
      { text: "Pour créer une boucle", isCorrect: false },
      { text: "Pour envoyer des tokens", isCorrect: false }
    ]
  }
];

// Fonction pour déterminer le niveau technique en fonction du score
const getTechnicalLevel = (score) => {
  if (score <= 1) return "débutant";
  if (score === 2) return "intermédiaire bas";
  if (score === 3) return "intermédiaire";
  if (score === 4) return "avancé";
  return "expert";
};

function Register() {
  const navigate = useNavigate();
  const [step, setStep] = useState("credentials"); // credentials, assessment, success
  const [form, setForm] = useState({ wallet: "", password: "" });
  const [answers, setAnswers] = useState(Array(technicalQuestions.length).fill(null));
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info"); // info / success / danger

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleAnswerChange = (questionIndex, optionIndex) => {
    const newAnswers = [...answers];
    newAnswers[questionIndex] = optionIndex;
    setAnswers(newAnswers);
  };

  const handleCredentialsSubmit = (e) => {
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

    // Passer à l'étape d'évaluation technique
    setMessage("");
    setStep("assessment");
  };

  const calculateScore = () => {
    let score = 0;
    answers.forEach((answer, index) => {
      if (answer !== null && technicalQuestions[index].options[answer].isCorrect) {
        score += 1;
      }
    });
    return score;
  };

  const handleAssessmentSubmit = async (e) => {
    e.preventDefault();

    // Calculer le score et le niveau
    const technicalScore = calculateScore();
    const technicalLevel = getTechnicalLevel(technicalScore);

    try {
      // Envoyer les données au backend
      await authAPI.register({
        ...form,
        technical_score: technicalScore,
        technical_level: technicalLevel
      });

      setMessage(`✅ Inscription réussie ! Votre niveau technique : ${technicalLevel} (${technicalScore}/5)`);
      setMessageType("success");
      setStep("success");
      setTimeout(() => navigate("/login"), 3000);
    } catch (error) {
      const errorMessage = handleApiError(error) || "❌ Erreur lors de l'inscription";
      setMessage(errorMessage);
      setMessageType("danger");
    }
  };

  // Affichage du formulaire d'identifiants
  if (step === "credentials") {
    return (
      <div className="d-flex justify-content-center align-items-center bg-light vh-100">
        <div className="card shadow-lg p-4 w-100" style={{ maxWidth: "400px" }}>
          <h2 className="text-center mb-4"><span role="img" aria-label="mémo">📝</span> Inscription</h2>
          <form onSubmit={handleCredentialsSubmit}>
            <div className="mb-3">
              <label className="form-label"><span role="img" aria-label="boîte aux lettres">📬</span> Adresse de portefeuille</label>
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
              <label className="form-label"><span role="img" aria-label="cadenas">🔒</span> Mot de passe</label>
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
            <button 
              type="submit" 
              className="btn btn-primary w-100" 
              style={{ 
                padding: "10px", 
                fontSize: "16px", 
                fontWeight: "bold",
                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
              }}
            >
              Continuer
            </button>
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

  // Affichage du questionnaire technique
  if (step === "assessment") {
    return (
      <div className="d-flex justify-content-center align-items-center bg-light min-vh-100 py-5">
        <div className="card shadow-lg p-4 w-100" style={{ maxWidth: "600px" }}>
          <h2 className="text-center mb-4"><span role="img" aria-label="cerveau">🧠</span> Évaluation technique</h2>
          <p className="text-center mb-4">Répondez aux 5 questions suivantes pour évaluer votre niveau en smart contracts Solidity et sécurité blockchain.</p>

          <form onSubmit={handleAssessmentSubmit}>
            {technicalQuestions.map((q, qIndex) => (
              <div key={qIndex} className="mb-4">
                <h5>{qIndex + 1}. {q.question}</h5>
                <div className="mt-2">
                  {q.options.map((option, oIndex) => (
                    <div key={oIndex} className="form-check mb-2">
                      <input
                        className="form-check-input"
                        type="radio"
                        name={`question-${qIndex}`}
                        id={`q${qIndex}-option${oIndex}`}
                        checked={answers[qIndex] === oIndex}
                        onChange={() => handleAnswerChange(qIndex, oIndex)}
                        required
                        style={{ 
                          width: "20px", 
                          height: "20px", 
                          cursor: "pointer",
                          border: "2px solid #007bff",
                          backgroundColor: answers[qIndex] === oIndex ? "#007bff" : "white",
                          accentColor: "#007bff"
                        }}
                      />
                      <label 
                        className="form-check-label" 
                        htmlFor={`q${qIndex}-option${oIndex}`}
                        style={{ 
                          cursor: "pointer", 
                          paddingLeft: "8px",
                          fontWeight: answers[qIndex] === oIndex ? "bold" : "normal"
                        }}
                      >
                        {option.text}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div className="d-flex justify-content-between mt-4">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={() => setStep("credentials")}
                style={{ 
                  padding: "10px 15px", 
                  fontSize: "16px", 
                  fontWeight: "bold",
                  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
                }}
              >
                Retour
              </button>
              <button 
                type="submit" 
                className="btn btn-success"
                disabled={answers.includes(null)}
                style={{ 
                  padding: "10px 15px", 
                  fontSize: "16px", 
                  fontWeight: "bold",
                  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
                }}
              >
                Terminer l'inscription
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Affichage du message de succès
  return (
    <div className="d-flex justify-content-center align-items-center bg-light vh-100">
      <div className="card shadow-lg p-4 w-100" style={{ maxWidth: "400px" }}>
        <h2 className="text-center mb-4"><span role="img" aria-label="coche verte">✅</span> Inscription terminée</h2>
        {message && (
          <div className={`alert alert-${messageType} mt-3 text-center`}>
            {message}
          </div>
        )}
        <p className="text-center">Redirection vers la page de connexion...</p>
      </div>
    </div>
  );
}

export default Register;
