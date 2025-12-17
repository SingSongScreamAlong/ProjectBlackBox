import React, { useState } from 'react';
import { TelemetryData } from '../../services/WebSocketService';
import TelemetryAnalysis from './TelemetryAnalysis';
import IncidentAnalysis from './IncidentAnalysis';
import TrainingGoals from '../Training/TrainingGoals';
import './AnalysisPage.css';

interface AnalysisPageProps {
  telemetryData: TelemetryData | null;
  sessionId?: string;
}

const AnalysisPage: React.FC<AnalysisPageProps> = ({ telemetryData, sessionId }) => {
  const [activeTab, setActiveTab] = useState<'telemetry' | 'incidents' | 'laps' | 'comparison' | 'training'>('telemetry');

  return (
    <div className="analysis-page">
      <div className="analysis-tabs">
        <button
          className={activeTab === 'telemetry' ? 'active' : ''}
          onClick={() => setActiveTab('telemetry')}
        >
          📈 Telemetry Graphs
        </button>
        <button
          className={activeTab === 'incidents' ? 'active' : ''}
          onClick={() => setActiveTab('incidents')}
        >
          ⚠️ Incident Analysis
        </button>
        <button
          className={activeTab === 'laps' ? 'active' : ''}
          onClick={() => setActiveTab('laps')}
        >
          🏁 Lap Comparison
        </button>
        <button
          className={activeTab === 'comparison' ? 'active' : ''}
          onClick={() => setActiveTab('comparison')}
        >
          👥 Driver Comparison
        </button>
        <button
          className={activeTab === 'training' ? 'active' : ''}
          onClick={() => setActiveTab('training')}
        >
          🎯 Training Goals
        </button>
      </div>

      <div className="analysis-content">
        {activeTab === 'telemetry' && (
          <TelemetryAnalysis telemetryData={telemetryData} />
        )}

        {activeTab === 'incidents' && (
          <IncidentAnalysis sessionId={sessionId} />
        )}

        {activeTab === 'laps' && (
          <div className="lap-comparison">
            <div className="comparison-header">
              <h3>Lap Time Comparison</h3>
              <div className="lap-selectors">
                <select defaultValue="best">
                  <option value="best">Best Lap</option>
                  <option value="last">Last Lap</option>
                  <option value="1">Lap 1</option>
                  <option value="2">Lap 2</option>
                  <option value="3">Lap 3</option>
                </select>
                <span>vs</span>
                <select defaultValue="theoretical">
                  <option value="theoretical">Theoretical Best</option>
                  <option value="reference">Reference Lap</option>
                  <option value="leader">Class Leader</option>
                </select>
              </div>
            </div>

            <div className="sector-comparison">
              <div style={{ textAlign: 'center', padding: '2rem', color: '#666', width: '100%' }}>
                Waiting for lap data...
              </div>
            </div>

            <div className="theoretical-best">
              <h4>Theoretical Best Lap</h4>
              <div className="theoretical-time">--:--.---</div>
              <div className="theoretical-breakdown">
                <span>S1: --.---</span>
                <span>S2: --.---</span>
                <span>S3: --.---</span>
              </div>
              <div className="potential-gain">
                Waiting for reference...
              </div>
            </div>
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="driver-comparison">
            <div className="comparison-header">
              <h3>Driver Comparison</h3>
              <div className="driver-selectors">
                <div style={{ color: '#888' }}>Waiting for competitors...</div>
              </div>
            </div>

            <div className="comparison-metrics">
              <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                Waiting for driver comparison data...
              </div>
            </div>

            <div className="comparison-insights">
              <h4>📊 Comparison Insights</h4>
              <ul>
                <li style={{ color: '#888', fontStyle: 'italic', listStyle: 'none' }}>Waiting for data...</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'training' && (
          <TrainingGoals />
        )}
      </div>
    </div>
  );
};

export default AnalysisPage;
