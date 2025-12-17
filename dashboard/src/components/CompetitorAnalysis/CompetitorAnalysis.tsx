import React from 'react';
import { CompetitorData, StrategyData } from '../../services/WebSocketService';

interface CompetitorAnalysisProps {
  competitorData: CompetitorData[] | null;
  strategyData: StrategyData | null;
}

const CompetitorAnalysis: React.FC<CompetitorAnalysisProps> = ({ competitorData, strategyData }) => {
  // Use provided data
  const displayCompetitorData = competitorData || [];
  const displayStrategyData = strategyData || {
    pitWindow: '-',
    optimalPit: '-',
    tireStrategy: '-',
    fuelStrategy: '-',
    paceTarget: '-',
    positionPrediction: '-',
    undercutRisk: '-',
    tireLife: 0
  };

  return (
    <div className="panel">
      <div className="panel-header">RACE STRATEGY & TIMING ANALYSIS</div>
      <div className="panel-content">
        <div className="strategy-grid">
          <div className={`strategy-item ${displayStrategyData.pitWindow !== '-' ? 'optimal' : ''}`}>
            <div className="stat-label">Pit Window</div>
            <div className="stat-value">{displayStrategyData.pitWindow}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Optimal Pit</div>
            <div className="stat-value">{displayStrategyData.optimalPit}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Tire Strategy</div>
            <div className="stat-value">{displayStrategyData.tireStrategy}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Fuel Strategy</div>
            <div className="stat-value">{displayStrategyData.fuelStrategy}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Pace Target</div>
            <div className="stat-value">{displayStrategyData.paceTarget}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Position Pred.</div>
            <div className="stat-value">{displayStrategyData.positionPrediction}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Undercut Risk</div>
            <div className="stat-value">{displayStrategyData.undercutRisk}</div>
          </div>
          <div className="strategy-item">
            <div className="stat-label">Tire Life</div>
            <div className="stat-value">{displayStrategyData.tireLife}%</div>
          </div>
        </div>

        {/* Sector Analysis - Placeholder until real sector data is available */}
        <div style={{ marginTop: '16px', textAlign: 'center', color: '#666' }}>
          <div className="section-title">SECTOR ANALYSIS</div>
          <div>Waiting for sector data...</div>
        </div>

        {/* Weather & Track Conditions - Placeholder */}
        <div style={{ marginTop: '16px', textAlign: 'center', color: '#666' }}>
          <div className="section-title">TRACK CONDITIONS</div>
          <div>Waiting for session info...</div>
        </div>
      </div>
    </div>
  );
};

export default CompetitorAnalysis;
