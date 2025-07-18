import React, { useState, useEffect, useContext } from "react";
import { Container, Card, Button, Table, Alert, Spinner, Modal, Form } from "react-bootstrap";
import { AuthContext } from "../contexts/AuthContext";
import { finetuneAPI } from "../services/api";
import axios from 'axios';

const POD_ID = process.env.REACT_APP_RUNPOD_ID || "r3etcvinyjvth2";
const FINETUNE_URL = `https://${POD_ID}-80.proxy.runpod.net/finetune-feedback`;

function Finetune() {
  const { token } = useContext(AuthContext);
  const [finetunes, setFinetunes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedFinetunes, setSelectedFinetunes] = useState([]);
  const [finetuning, setFinetuning] = useState(false);
  const [finetuneResult, setFinetuneResult] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchFinetunes();
  }, [currentPage]);

  const fetchFinetunes = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch finetune entries from the API
      const response = await finetuneAPI.list({ 
        page: currentPage, 
        per_page: 20 
      });

      // Filter only entries that have feedback_user
      const itemsWithFeedback = (response.data.data.items || []).filter(item => item.feedback_user);
      setFinetunes(itemsWithFeedback);
      setTotalPages(response.data.data.pagination?.pages || 1);
    } catch (err) {
      console.error("Erreur lors de la récupération des finetunes:", err);
      setError("Impossible de charger les données de finetune. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFinetune = (finetune) => {
    setSelectedFinetunes(prev => {
      const isSelected = prev.some(f => f.id === finetune.id);
      if (isSelected) {
        return prev.filter(f => f.id !== finetune.id);
      } else {
        return [...prev, finetune];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedFinetunes.length === finetunes.length) {
      setSelectedFinetunes([]);
    } else {
      setSelectedFinetunes(finetunes);
    }
  };

  const prepareFinetuneData = () => {
    return selectedFinetunes.map(finetune => ({
      // Question is the combination of user input and model response
      question: `${finetune.user_input}\n\nModel Response:\n${finetune.model_outputs}`,
      // Answer is the user feedback
      answer: finetune.feedback_user,
      // Weight from the finetune entry
      weight: finetune.weight_request || 1.0
    }));
  };

  const handleFinetune = async () => {
    try {
      setFinetuning(true);
      setFinetuneResult(null);
      
      const data = prepareFinetuneData();
      
      const response = await axios.post(FINETUNE_URL, data, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setFinetuneResult({
        success: true,
        message: "Le fine-tuning a été lancé avec succès!",
        data: response.data
      });
      
      setShowModal(false);
      setSelectedFinetunes([]);
    } catch (err) {
      console.error("Erreur lors du lancement du fine-tuning:", err);
      setFinetuneResult({
        success: false,
        message: "Erreur lors du lancement du fine-tuning. Veuillez réessayer.",
        error: err.message
      });
    } finally {
      setFinetuning(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    if (!status) return <span className="badge bg-secondary">Non défini</span>;
    
    const statusMap = {
      'pending': { color: 'warning', label: 'En attente' },
      'approved': { color: 'success', label: 'Approuvé' },
      'rejected': { color: 'danger', label: 'Rejeté' },
      'under_review': { color: 'info', label: 'En révision' }
    };
    
    const statusInfo = statusMap[status] || { color: 'secondary', label: status };
    return <span className={`badge bg-${statusInfo.color}`}>{statusInfo.label}</span>;
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return "-";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: "400px" }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Chargement...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container className="mt-4 mb-5">
      <Card>
        <Card.Header className="bg-primary text-white">
          <h4 className="mb-0">🎯 Fine-tuning du modèle</h4>
        </Card.Header>
        <Card.Body>
          {error && (
            <Alert variant="danger" onClose={() => setError(null)} dismissible>
              {error}
            </Alert>
          )}

          {finetuneResult && (
            <Alert 
              variant={finetuneResult.success ? "success" : "danger"} 
              onClose={() => setFinetuneResult(null)} 
              dismissible
            >
              {finetuneResult.message}
            </Alert>
          )}

          <div className="mb-3">
            <p className="text-muted">
              Sélectionnez les feedbacks à utiliser pour le fine-tuning du modèle. 
              Le système va entraîner le modèle à répondre selon les feedbacks fournis par les utilisateurs.
            </p>
          </div>

          {finetunes.length === 0 ? (
            <Alert variant="info">
              Aucun feedback disponible pour le fine-tuning. Les feedbacks sont créés lorsque les utilisateurs commentent les analyses.
            </Alert>
          ) : (
            <>
              <div className="mb-3 d-flex justify-content-between align-items-center">
                <div>
                  <Button 
                    variant="outline-primary" 
                    size="sm"
                    onClick={handleSelectAll}
                  >
                    {selectedFinetunes.length === finetunes.length ? "Tout désélectionner" : "Tout sélectionner"}
                  </Button>
                  <span className="ms-3 text-muted">
                    {selectedFinetunes.length} feedback{selectedFinetunes.length > 1 ? 's' : ''} sélectionné{selectedFinetunes.length > 1 ? 's' : ''}
                  </span>
                </div>
                <Button 
                  variant="primary"
                  disabled={selectedFinetunes.length === 0}
                  onClick={() => setShowModal(true)}
                >
                  Lancer le Fine-tuning
                </Button>
              </div>

              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th style={{ width: "50px" }}>
                      <Form.Check 
                        type="checkbox"
                        checked={selectedFinetunes.length === finetunes.length && finetunes.length > 0}
                        onChange={handleSelectAll}
                      />
                    </th>
                    <th>Requête utilisateur</th>
                    <th>Réponse du modèle</th>
                    <th>Feedback utilisateur</th>
                    <th>Statut</th>
                    <th>Poids</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {finetunes.map((finetune) => (
                    <tr key={finetune.id}>
                      <td>
                        <Form.Check 
                          type="checkbox"
                          checked={selectedFinetunes.some(f => f.id === finetune.id)}
                          onChange={() => handleSelectFinetune(finetune)}
                        />
                      </td>
                      <td title={finetune.user_input}>
                        {truncateText(finetune.user_input, 40)}
                      </td>
                      <td title={finetune.model_outputs}>
                        {truncateText(finetune.model_outputs, 40)}
                      </td>
                      <td title={finetune.feedback_user}>
                        <strong>{truncateText(finetune.feedback_user, 40)}</strong>
                      </td>
                      <td>{getStatusBadge(finetune.feedback_status)}</td>
                      <td>{finetune.weight_request.toFixed(2)}</td>
                      <td>{formatDate(finetune.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="d-flex justify-content-center mt-3">
                  <Button 
                    variant="outline-primary" 
                    size="sm" 
                    className="me-2"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  >
                    Précédent
                  </Button>
                  <span className="align-self-center mx-3">
                    Page {currentPage} sur {totalPages}
                  </span>
                  <Button 
                    variant="outline-primary" 
                    size="sm" 
                    className="ms-2"
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  >
                    Suivant
                  </Button>
                </div>
              )}
            </>
          )}
        </Card.Body>
      </Card>

      {/* Modal de confirmation */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirmer le Fine-tuning</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Vous êtes sur le point de lancer un fine-tuning avec <strong>{selectedFinetunes.length}</strong> feedback{selectedFinetunes.length > 1 ? 's' : ''}.</p>
          
          <div className="mt-3">
            <h6>Résumé :</h6>
            <ul>
              <li>Feedbacks approuvés : {selectedFinetunes.filter(f => f.feedback_status === "approved").length}</li>
              <li>Feedbacks en attente : {selectedFinetunes.filter(f => f.feedback_status === "pending").length}</li>
              <li>Feedbacks rejetés : {selectedFinetunes.filter(f => f.feedback_status === "rejected").length}</li>
              <li>Poids total : {selectedFinetunes.reduce((sum, f) => sum + f.weight_request, 0).toFixed(2)}</li>
            </ul>
          </div>
          
          <Alert variant="info" className="mt-3">
            <strong>Note :</strong> Le modèle sera entraîné à produire des réponses similaires aux feedbacks fournis par les utilisateurs.
          </Alert>
          
          <p className="text-muted mt-3">
            Cette opération peut prendre plusieurs minutes. Voulez-vous continuer ?
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)} disabled={finetuning}>
            Annuler
          </Button>
          <Button variant="primary" onClick={handleFinetune} disabled={finetuning}>
            {finetuning ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Lancement en cours...
              </>
            ) : (
              "Lancer le Fine-tuning"
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default Finetune;