import React from 'react';
import './AnalysisDisplay.css';

const AnalysisDisplay = ({ analysisData, reportData, showProgress, onRestartAnalysis }) => {

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
          <h2>Tableau d’avancement</h2>
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
          <h2>Tableau détaillé final</h2>

          <div className={`report-section global-info ${reportData.globalStatus === 'OK' ? 'status-ok' : 'status-ko'}`}>
            <h3>Informations globales</h3>
            <p><strong>Nom du fichier:</strong> {reportData.fileName}</p>
            <p><strong>Nom du contrat:</strong> {reportData.contractName}</p>
            <p><strong>Adresse déployée:</strong> {reportData.deployedAddress}</p>
            <p><strong>Version du compilateur Solidity:</strong> {reportData.compilerVersion}</p>
            <p><strong>Date d’analyse:</strong> {reportData.analysisDate}</p>
            <p><strong>Statut global:</strong> <span className={reportData.globalStatus === 'OK' ? 'status-ok-text' : 'status-ko-text'}>{reportData.globalStatus}</span></p>
          </div>

          <div className={`report-section global-result ${reportData.globalStatus === 'OK' ? 'status-ok' : 'status-ko'}`}>
            <h3>Résultat global</h3>
            <p><strong>Statut:</strong> <span className={reportData.globalStatus === 'OK' ? 'status-ok-text' : 'status-ko-text'}>{reportData.globalStatus === 'OK' ? '✅ OK' : `❌ KO – ${reportData.vulnerabilityType || 'Vulnérabilité détectée'}`}</span></p>
            {reportData.vulnerabilityType && <p><strong>Type de vulnérabilité:</strong> {reportData.vulnerabilityType}</p>}
          </div>

          <div className="report-section analysis-summary">
            <h3>Résumé de l’analyse</h3>
            <ul>
              {reportData.analysisSummary && reportData.analysisSummary.map((item, index) => (
                <li key={index} className={item.isCritical ? 'critical-point' : ''}>{item.point}</li>
              ))}
            </ul>
          </div>

          <div className="report-section model-reasoning">
            <h3>Raisonnement du modèle</h3>
            <div dangerouslySetInnerHTML={{ __html: reportData.modelReasoning }} />
            {/* For code snippets:
            <pre className="code-snippet">
              <code>{reportData.codeSnippet}</code>
            </pre>
            */}
          </div>

          {reportData.exploitCode && (
            <div className="report-section exploit-code">
              <h3>⚔️ Code d’exploit</h3>
              <pre className="code-block">
                <code>{reportData.exploitCode}</code>
              </pre>
              <button onClick={() => navigator.clipboard.writeText(reportData.exploitCode)}>Copier</button>
            </div>
          )}

          <button onClick={onRestartAnalysis} className="restart-button">Relancer l'analyse</button>
          {/* Placeholder for download button */}
          <button className="download-button">Télécharger le rapport</button>
        </div>
      )}
    </div>
  );
};

export default AnalysisDisplay;
