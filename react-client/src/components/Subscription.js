import React, { useContext, useState, useEffect } from "react";
import { AuthContext } from "../contexts/AuthContext";
import { subscriptionAPI } from "../services/api";

function Subscription() {
  const { token } = useContext(AuthContext);
  const [currentPlan, setCurrentPlan] = useState("free");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch current plan on component mount
  useEffect(() => {
    const fetchCurrentPlan = async () => {
      try {
        setLoading(true);
        // In a real app, this would call the API
        // const response = await subscriptionAPI.getCurrentPlan();
        // setCurrentPlan(response.data.planId);

        // For demo purposes, we'll just use a mock value
        setTimeout(() => {
          setCurrentPlan("free");
          setLoading(false);
        }, 500);
      } catch (err) {
        console.error("Error fetching current plan:", err);
        setError("Impossible de récupérer votre plan d'abonnement actuel.");
        setLoading(false);
      }
    };

    fetchCurrentPlan();
  }, []);

  // Handle subscription - show information popup about temporary free access
  const handleSubscribe = async (planId, planName) => {
    try {
      // Show information popup about temporary free access
      alert("ℹ️ Accès temporaire gratuit\nPour le moment, vous avez accès à toutes les fonctionnalités gratuitement.\n\n🛠️ Dans les prochains jours, nous mettrons en place un système d'abonnement avec paiement par carte bancaire ou crypto.\n\nMerci pour votre soutien 🙏");

      // In a real app, this would call the API
      // await subscriptionAPI.subscribe(planId, paymentMethod);

      // Mock successful subscription
      // setCurrentPlan(planId);
    } catch (err) {
      console.error("Error subscribing to plan:", err);
      setError("Une erreur est survenue lors de l'abonnement. Veuillez réessayer.");
    }
  };

  // Plans data
  const plans = [
    {
      id: "free",
      name: "Gratuit",
      price: "0€",
      color: "bg-light",
      features: [
        { text: "5 analyses / mois" },
        { text: "Résultats basiques" },
        { text: "Pas d'historique" }
      ],
      buttonText: "Plan actuel",
      buttonVariant: "outline-secondary",
      recommended: false
    },
    {
      id: "starter",
      name: "Starter",
      price: "5€/mois",
      color: "bg-info bg-opacity-10",
      features: [
        { text: "30 analyses / mois" },
        { text: "Résultats détaillés" },
        { text: "Historique utilisateur" },
        { text: "Paiement CB ou crypto" }
      ],
      buttonText: "S'abonner",
      buttonVariant: "info",
      recommended: false
    },
    {
      id: "pro",
      name: "Pro",
      price: "15€/mois",
      color: "bg-primary bg-opacity-10",
      features: [
        { text: "100 analyses / mois" },
        { text: "Détails complets sur les failles" },
        { text: "Suggestions IA" },
        { text: "Export PDF" },
        { text: "Support prioritaire" }
      ],
      buttonText: "S'abonner",
      buttonVariant: "primary",
      recommended: true
    },
    {
      id: "enterprise",
      name: "Entreprise",
      price: "Sur devis",
      color: "bg-dark bg-opacity-10",
      features: [
        { text: "Analyses illimitées" },
        { text: "Accès à l'API" },
        { text: "Intégration sur mesure" },
        { text: "Support dédié" }
      ],
      buttonText: "Contacter",
      buttonVariant: "dark",
      recommended: false
    }
  ];

  // Loading and error states
  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Chargement...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mt-5">
      <h2 className="text-center mb-5">
        Nos offres d'abonnement
      </h2>

      <div className="row row-cols-1 row-cols-md-2 row-cols-lg-4 g-4 mb-5">
        {plans.map((plan) => (
          <div className="col" key={plan.id}>
            <div 
              className={`card h-100 ${plan.color} border-0 shadow-sm`}
              style={{ 
                transition: "transform 0.3s, box-shadow 0.3s",
                background: plan.recommended ? "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)" : "",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = "translateY(-5px)";
                e.currentTarget.style.boxShadow = "0 10px 20px rgba(0,0,0,0.1)";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 0.125rem 0.25rem rgba(0,0,0,0.075)";
              }}
            >
              <div className="card-header bg-transparent border-0 text-center pt-4 position-relative">
                {plan.recommended && (
                  <div 
                    className="position-absolute top-0 end-0 badge bg-success m-2"
                    style={{ transform: "rotate(10deg)" }}
                  >
                    Recommandé
                  </div>
                )}
                <h3 className="card-title">{plan.name}</h3>
                <div className="display-6 my-3">{plan.price}</div>
              </div>
              <div className="card-body">
                <ul className="list-unstyled">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="mb-2">
                      <span>{feature.text}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="card-footer bg-transparent border-0 text-center pb-4">
                <button 
                  className={`btn btn-${plan.buttonVariant} px-4 py-2`}
                  onClick={() => handleSubscribe(plan.id, plan.name)}
                  disabled={currentPlan === plan.id}
                >
                  {currentPlan === plan.id ? "Plan actuel" : plan.buttonText}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="row justify-content-center">
        <div className="col-md-8">
          <div className="card mb-5 border-0 shadow-sm">
            <div className="card-body p-4">
              <h4 className="card-title">
                <span role="img" aria-label="information">ℹ️</span> Informations sur les paiements
              </h4>
              <p>
                Nous acceptons les paiements par carte bancaire via Stripe et les paiements en cryptomonnaie via WalletConnect.
                Tous les abonnements sont renouvelés automatiquement et peuvent être annulés à tout moment.
              </p>
              <div className="d-flex gap-3 mt-4">
                <div className="bg-light p-3 rounded">
                  <span role="img" aria-label="carte bancaire" className="me-2">💳</span>
                  <span>Paiement par carte</span>
                </div>
                <div className="bg-light p-3 rounded">
                  <span role="img" aria-label="cryptomonnaie" className="me-2">🪙</span>
                  <span>Paiement en crypto</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Subscription;
