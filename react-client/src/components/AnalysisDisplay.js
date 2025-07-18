import React, {useContext} from 'react';
import './AnalysisDisplay.css';
import {downloadBlob, getUserFromToken, handleApiError} from "../utils/utils";
import {contractAPI} from "../services/api";
import {AuthContext} from "../contexts/AuthContext";
import Tooltip from './Tooltip'; // Importez le composant Tooltip



const AnalysisDisplay = ({ analysisData, reportData, showProgress, onRestartAnalysis }) => {
    const { token } = useContext(AuthContext);
    const handleReportDownload = (filename) => {
        const userData = getUserFromToken(token);
        if (!userData || !userData.wallet) {
          alert("Erreur: Impossible d'extraire les informations utilisateur du token");
          return;
        }

        contractAPI.getReport(userData.wallet, filename)
          .then(res => {
            downloadBlob(res.data, `${filename}.txt`);
          })
          .catch(error => {
            alert(`Erreur lors du téléchargement: ${handleApiError(error)}`);
          });
    };
  // const progressSteps = [ // This can be removed as Analyze.js sends the full list of steps and their states
  //   { name: 'Vérification du format Solidity', status: 'pending', icon: '⏳' },
  //   { name: 'Compilation du contrat', status: 'pending', icon: '⏳' },
  //   { name: 'Analyse des fonctions', status: 'pending', icon: '⏳' },
  //   { name: 'Détection de vulnérabilités', status: 'pending', icon: '⏳' },
  //   { name: 'Génération du rapport final', status: 'pending', icon: '⏳' },
  // ];

  // This function is no longer strictly needed if we iterate over analysisData.steps directly
  // const getStepStatus = (stepName) => {
  //   if (analysisData && analysisData.steps && analysisData.steps[stepName]) {
  //     return analysisData.steps[stepName];
  //   }
  //   return { status: 'pending', icon: '⏳', color: 'blue' }; // Should not be reached if Analyze.js initializes all steps
  // };

  return (
    <div className="analysis-display">
      {showProgress && analysisData && analysisData.steps && (
        <div className="progress-table">
          <Tooltip text="Ce tableau montre l'état d'avancement de l'analyse en cours. Chaque étape est mise à jour en temps réel pour vous permettre de suivre la progression.">
            <h2>Tableau d'avancement</h2>
          </Tooltip>
          <table>
            <thead>
              <tr>
                <th>Étape</th>
                <th>Statut</th>
                <th>Icône</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(analysisData.steps).map(([stepName, stepData], index) => {
                let statusClass = '';
                if (stepData.status === 'Terminé') statusClass = 'status-completed';
                else if (stepData.status === 'Échec') statusClass = 'status-failed';
                else if (stepData.status === 'En cours') statusClass = 'status-in-progress';
                else statusClass = 'status-pending'; // Or derive from stepData.color

                return (
                  <tr key={index}>
                    <td>{stepName}</td>
                    <td className={statusClass}>{stepData.status}</td>
                    <td>{stepData.icon}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!showProgress && reportData && (
        <div className="final-report">
          <Tooltip text="Ce tableau présente un résumé détaillé de l'analyse du contrat intelligent, incluant les informations sur le financement, l'exécution et le résultat de l'attaque.">
            <h2>Tableau détaillé final</h2>
          </Tooltip>

          {!reportData.isServiceError && (
            <div className="report-section guide">
              <Tooltip text="Cette section explique comment lire et interpréter les différentes parties du rapport d'analyse.">
                <h3>Guide de lecture du rapport</h3>
              </Tooltip>
              <div className="guide-container">
                <table className="guide-table">
                  <thead>
                    <tr>
                      <th>Section</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Informations globales</strong></td>
                      <td>Métadonnées du contrat analysé (nom, adresse, version du compilateur)</td>
                    </tr>
                    <tr>
                      <td><strong>Résultat global</strong></td>
                      <td>Verdict final de l'analyse : SÉCURISÉ ou VULNÉRABLE</td>
                    </tr>
                    <tr>
                      <td><strong>Résumé de l'analyse</strong></td>
                      <td>Points clés et vulnérabilités identifiées dans le contrat</td>
                    </tr>
                    <tr>
                      <td><strong>Détails techniques</strong></td>
                      <td>Analyse approfondie des vulnérabilités et de leur impact</td>
                    </tr>
                    <tr>
                      <td><strong>Code d'exploit</strong></td>
                      <td>Démonstration technique de l'exploitation de la vulnérabilité (si applicable)</td>
                    </tr>
                    <tr>
                      <td><strong>Contrat financé</strong></td>
                      <td>Indique si le contrat a été financé avec succès pour les tests d'attaque</td>
                    </tr>
                    <tr>
                      <td><strong>Attaque exécutée</strong></td>
                      <td>Indique si une attaque a été tentée sur le contrat</td>
                    </tr>
                    <tr>
                      <td><strong>Attaque réussie</strong></td>
                      <td>Indique si l'attaque a réussi à exploiter une vulnérabilité</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {reportData.isServiceError ? (
            <div className="report-section service-error">
              <h3>Erreur de service</h3>
              <div className="alert alert-danger">
                <h4 className="alert-heading">
                  {reportData.errorType === 'runpod_unavailable' && '❌ Analyse non terminée — Runpod indisponible'}
                  {reportData.errorType === 'llm_unavailable' && '❌ Erreur critique — LLM backend unreachable'}
                  {reportData.errorType === 'slither_failed' && '❌ Erreur d\'analyse — L\'analyse Slither a échoué'}
                  {reportData.errorType === 'server_error' && '❌ Erreur serveur — Le service d\'analyse est temporairement indisponible'}
                  {!['runpod_unavailable', 'llm_unavailable', 'slither_failed', 'server_error'].includes(reportData.errorType) && '❌ Erreur d\'analyse'}
                </h4>
                <p>
                  {reportData.errorType === 'runpod_unavailable' && 'Le service Runpod n\'est pas disponible. Veuillez réessayer plus tard.'}
                  {reportData.errorType === 'llm_unavailable' && 'Le service LLM n\'est pas accessible. Veuillez réessayer plus tard.'}
                  {reportData.errorType === 'slither_failed' && 'L\'analyse Slither a échoué. Veuillez vérifier votre code et réessayer.'}
                  {reportData.errorType === 'server_error' && 'Le serveur d\'analyse a rencontré une erreur. Veuillez réessayer plus tard.'}
                  {!['runpod_unavailable', 'llm_unavailable', 'slither_failed', 'server_error'].includes(reportData.errorType) && 'Une erreur s\'est produite lors de l\'analyse. Veuillez réessayer.'}
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className={`report-section global-info ${reportData.globalStatus === 'OK' ? 'status-ok' : 'status-ko'}`}>
                <Tooltip text="Cette section contient les métadonnées du contrat analysé, comme son nom, son adresse de déploiement et la version du compilateur utilisée.">
                  <h3>Informations globales</h3>
                </Tooltip>
                <p><strong>Nom du fichier:</strong> {reportData.fileName}</p>
                <p><strong>Nom du contrat:</strong> {reportData.contractName}</p>
                <p><strong>Adresse déployée:</strong> {reportData.contractAddress}</p>
                <p><strong>Version du compilateur Solidity:</strong> {reportData.compilerVersion}</p>
                <p><strong>Date d'analyse:</strong> {reportData.analysisDate}</p>
                <p><strong>Statut global:</strong> <span className={reportData.globalStatus === 'OK' ? 'status-ok-text' : 'status-ko-text'}>{reportData.globalStatus}</span></p>
              </div>

              <div className={`report-section global-result ${reportData.globalStatus === 'OK' ? 'status-ok' : 'status-ko'}`}>
                <Tooltip text="Cette section indique si le contrat est sécurisé ou vulnérable. Un statut 'SÉCURISÉ' signifie qu'aucune vulnérabilité critique n'a été détectée, tandis qu'un statut 'VULNÉRABLE' indique qu'au moins une vulnérabilité a été identifiée.">
                  <h3>Résultat global</h3>
                </Tooltip>
                <div className="status-badge-container">
                  {reportData.globalStatus === 'OK' ? (
                    <div className="status-badge status-badge-ok">
                      <span className="badge-icon">✅</span>
                      <span className="badge-text">SÉCURISÉ</span>
                    </div>
                  ) : (
                    <div className="status-badge status-badge-ko">
                      <span className="badge-icon">❌</span>
                      <span className="badge-text">VULNÉRABLE</span>
                    </div>
                  )}
                  {reportData.vulnerabilityType && reportData.globalStatus !== 'OK' && (
                    <div className="vulnerability-type-badge">
                      {reportData.vulnerabilityType}
                    </div>
                  )}
                </div>
                <p className="status-description">
                  {reportData.globalStatus === 'OK' 
                    ? 'Aucune vulnérabilité critique détectée dans ce contrat.' 
                    : `Une vulnérabilité de type "${reportData.vulnerabilityType || 'Non spécifiée'}" a été identifiée.`}
                </p>
              </div>
            </>
          )}

          <div className="report-section analysis-summary">
            <Tooltip text="Cette section présente les points clés de l'analyse, mettant en évidence les vulnérabilités potentielles et les caractéristiques importantes du contrat. Les éléments critiques sont marqués d'un symbole d'avertissement.">
              <h3>Résumé de l'analyse</h3>
            </Tooltip>
            <div className="summary-container">
              {reportData.analysisSummary && reportData.analysisSummary.map((item, index) => (
                <div key={index} className={`summary-item ${item.isCritical ? 'summary-item-critical' : 'summary-item-normal'}`}>
                  <div className="summary-icon">
                    {item.isCritical ? '⚠️' : '📌'}
                  </div>
                  <div className="summary-content">
                    <p>{item.point}</p>
                    {item.isCritical && reportData.vulnerabilityType && (
                      <div className="summary-impact">
                        <strong>Impact:</strong> Cette vulnérabilité de type {reportData.vulnerabilityType} peut compromettre la sécurité du contrat.
                      </div>
                    )}
                    {item.isCritical && (
                      <div className="summary-recommendation">
                        <strong>Recommandation:</strong> {
                          reportData.vulnerabilityType === "Reentrancy" 
                            ? "Utiliser le pattern checks-effects-interactions et/ou des mutex pour prévenir les réentrances."
                            : reportData.vulnerabilityType === "Integer Overflow/Underflow" 
                              ? "Utiliser SafeMath ou des versions récentes de Solidity (0.8+) avec vérification automatique."
                              : reportData.vulnerabilityType === "Access Control" 
                                ? "Implémenter des contrôles d'accès stricts et des modificateurs de fonction appropriés."
                                : "Consulter un auditeur de sécurité pour résoudre cette vulnérabilité."
                        }
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="report-section model-reasoning">
            <Tooltip text="Cette section fournit une analyse technique approfondie du contrat, expliquant en détail les vulnérabilités identifiées, leur cause et leur impact potentiel sur la sécurité du contrat.">
              <h3>Détails techniques</h3>
            </Tooltip>
            <div className="reasoning-container">
              <div className="reasoning-header">
                <div className="reasoning-icon">🔍</div>
                <div className="reasoning-title">Analyse technique détaillée</div>
              </div>
              <div className="reasoning-content">
                <div dangerouslySetInnerHTML={{ __html: reportData.modelReasoning }} />
              </div>
              {reportData.globalStatus !== 'OK' && (
                <div className="reasoning-footer">
                  <div className="reasoning-note">
                    <strong>Note:</strong> Cette analyse a été générée automatiquement et identifie les vulnérabilités potentielles dans le code du contrat.
                  </div>
                </div>
              )}
            </div>
          </div>

          {reportData.globalStatus !== 'OK' && (
            <div className="report-section exploit-code">
              <Tooltip text="Cette section présente un code d'exploitation (Proof of Concept) qui démontre comment la vulnérabilité identifiée pourrait être exploitée. Ce code est fourni uniquement à des fins éducatives et ne doit pas être utilisé en production.">
                <h3>⚔️ Code d'exploit</h3>
              </Tooltip>
              {reportData.exploitCode && reportData.exploitCode.trim() !== '' && reportData.exploitCode !== 'function exploit() public payable {}' ? (
                <>
                  <div className="exploit-header">
                    <div className="exploit-badge">POC</div>
                    <div className="exploit-warning">
                      <span className="warning-icon">⚠️</span>
                      <span>Ce code est fourni à des fins éducatives uniquement. Ne pas utiliser en production.</span>
                    </div>
                  </div>
                  <pre className="code-block">
                    <code>{reportData.exploitCode}</code>
                  </pre>
                  <div className="exploit-actions">
                    <button 
                      className="exploit-button copy-button"
                      onClick={() => navigator.clipboard.writeText(reportData.exploitCode)}
                    >
                      <span className="button-icon">📋</span> Copier le code
                    </button>
                    <button 
                      className="exploit-button download-button"
                      onClick={() => {
                        const blob = new Blob([reportData.exploitCode], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `exploit_${reportData.contractName.replace(/\s+/g, '_')}.sol`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <span className="button-icon">⬇️</span> Télécharger
                    </button>
                  </div>
                </>
              ) : (
                <div className="no-exploit-message">
                  <p>
                    <span className="info-icon">ℹ️</span>
                    Aucun code d'exploit n'a été généré pour cette vulnérabilité.
                  </p>
                  <p className="no-exploit-note">
                    Cela peut être dû à la complexité de la vulnérabilité ou à l'absence de vecteur d'attaque exploitable automatiquement.
                    Consultez la section "Détails techniques" pour plus d'informations.
                  </p>
                </div>
              )}
            </div>
          )}

          <button onClick={onRestartAnalysis} className="restart-button">Relancer l'analyse</button>
          {/* Download button - disabled for service errors */}
          {!reportData.isServiceError ? (

            <button onClick={() => {
                console.log(reportData, analysisData);
                if (reportData.rawReport && reportData.rawReport.filename) {
                    handleReportDownload(reportData.rawReport.filename);
                } else {
                    alert("Erreur: Impossible de télécharger le rapport, informations manquantes.");
                }
            }} className="download-button">Télécharger le rapport</button>
          ) : (
            <button className="download-button" disabled title="Téléchargement indisponible en raison d'une erreur de service">
              Télécharger le rapport
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalysisDisplay;
