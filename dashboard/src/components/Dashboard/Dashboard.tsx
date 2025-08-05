import React, { useEffect, useState } from 'react';
import Header from '../Header/Header';
import Telemetry from '../Telemetry/Telemetry';
import TrackMap from '../TrackMap/TrackMap';
import AICoaching from '../AICoaching/AICoaching';
import VideoPanel from '../VideoPanel/VideoPanel';
import CompetitorAnalysis from '../CompetitorAnalysis/CompetitorAnalysis';
import CompetitorPositions from '../CompetitorAnalysis/CompetitorPositions';
import MultiDriverPanel from '../MultiDriver/MultiDriverPanel';
import webSocketService from '../../services/WebSocketService';
import { 
  TelemetryData, 
  CoachingInsight, 
  DriverSkillAnalysis, 
  CompetitorData, 
  StrategyData,
  SessionInfo
} from '../../services/WebSocketService';

const Dashboard: React.FC = () => {
  // State for all dashboard data
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [coachingInsights, setCoachingInsights] = useState<CoachingInsight[] | null>(null);
  const [skillAnalysis, setSkillAnalysis] = useState<DriverSkillAnalysis | null>(null);
  const [competitorData, setCompetitorData] = useState<CompetitorData[] | null>(null);
  const [strategyData, setStrategyData] = useState<StrategyData | null>(null);
  const [showMultiDriverPanel, setShowMultiDriverPanel] = useState<boolean>(false);
  // Create a compatible SessionInfo state that matches the interface
  const [sessionInfo, setSessionInfo] = useState<SessionInfo>({
    track: 'Silverstone',
    session: 'RACE',
    driver: 'PLAYER',
    car: 'Ferrari SF24',
    weather: {
      temperature: 28,
      trackTemperature: 42,
      windSpeed: 12,
      windDirection: 'NW',
      humidity: 65,
      trackGrip: 95
    },
    totalLaps: 52,
    sessionTime: 0,
    remainingTime: 3600
  });
  
  // Additional display state for UI elements
  const [displayInfo, setDisplayInfo] = useState({
    trackName: 'Silverstone',
    sessionType: 'RACE',
    lapCount: 12
  });
  const [connected, setConnected] = useState<boolean>(false);

  // Initialize WebSocket connection
  useEffect(() => {
    // Create WebSocket service instance
    // Use the exported singleton instance directly
    const wsService = webSocketService;
    
    const handleConnect = () => {
      console.log('Connected to WebSocket server');
      setConnected(true);
    };
    
    const handleDisconnect = () => {
      console.log('Disconnected from WebSocket server');
      setConnected(false);
    };
    
    const handleTelemetryUpdate = (data: TelemetryData) => {
      console.log('Telemetry data received:', data);
      setTelemetryData(data);
    };
    
    const handleCoachingUpdate = (insights: CoachingInsight[]) => {
      console.log('Coaching insights received:', insights);
      setCoachingInsights(insights);
    };
    
    const handleSkillAnalysisUpdate = (analysis: DriverSkillAnalysis) => {
      console.log('Skill analysis received:', analysis);
      setSkillAnalysis(analysis);
    };
    
    const handleCompetitorUpdate = (data: CompetitorData[]) => {
      console.log('Competitor data received:', data);
      setCompetitorData(data);
    };
    
    const handleStrategyUpdate = (data: StrategyData) => {
      console.log('Strategy data received:', data);
      setStrategyData(data);
    };
    
    const handleSessionUpdate = (data: Partial<SessionInfo>) => {
      console.log('Session info received:', data);
      setSessionInfo(prevState => ({
        ...prevState,
        ...data
      }));
    };
    
    // Subscribe to events and store unsubscribe functions
    const unsubscribeConnect = wsService.on('connect', handleConnect).unsubscribe;
    const unsubscribeDisconnect = wsService.on('disconnect', handleDisconnect).unsubscribe;
    const unsubscribeTelemetry = wsService.on('telemetry', handleTelemetryUpdate).unsubscribe;
    const unsubscribeCoaching = wsService.on('coaching', handleCoachingUpdate).unsubscribe;
    const unsubscribeSkillAnalysis = wsService.on('skill_analysis', handleSkillAnalysisUpdate).unsubscribe;
    const unsubscribeCompetitorData = wsService.on('competitor_data', handleCompetitorUpdate).unsubscribe;
    const unsubscribeStrategyData = wsService.on('strategy_data', handleStrategyUpdate).unsubscribe;
    const unsubscribeSessionInfo = wsService.on('session_info', handleSessionUpdate).unsubscribe;
    
    // Connect to WebSocket server
    wsService.connect();
    
    // Clean up event listeners on unmount
    return () => {
      // Call all unsubscribe functions
      unsubscribeConnect();
      unsubscribeDisconnect();
      unsubscribeTelemetry();
      unsubscribeCoaching();
      unsubscribeSkillAnalysis();
      unsubscribeCompetitorData();
      unsubscribeStrategyData();
      unsubscribeSessionInfo();
      wsService.disconnect();
    };
  }, []);

  return (
    <div className="dashboard">
      <Header 
        connected={connected}
        sessionInfo={{
          trackName: sessionInfo.track || 'Unknown Track',
          sessionType: sessionInfo.session || 'Unknown',
          lapCount: displayInfo.lapCount,
          totalLaps: sessionInfo.totalLaps || 0,
          driverName: sessionInfo.driver || 'Unknown Driver',
          carName: sessionInfo.car || 'Unknown Car',
          // Convert weather object to string for Header component
          weather: typeof sessionInfo.weather === 'object' && sessionInfo.weather !== null ? 
            `${sessionInfo.weather.temperature}°C, ${sessionInfo.weather.humidity}% Humidity` : 
            'Unknown'
        }}
        onMultiDriverClick={() => setShowMultiDriverPanel(!showMultiDriverPanel)}
      />
      
      <div className="dashboard-grid">
        <div className="dashboard-left">
          <Telemetry telemetryData={telemetryData} />
          <TrackMap telemetryData={telemetryData} trackName={sessionInfo.track || 'Unknown Track'} />
        </div>
        
        <div className="dashboard-center">
          <AICoaching 
            insights={coachingInsights} 
            skillAnalysis={skillAnalysis} 
          />
          <VideoPanel 
            driverCamActive={true} 
            spotterCamActive={true} 
          />
        </div>
        
        <div className="dashboard-right">
          <CompetitorPositions competitorData={competitorData} />
          <CompetitorAnalysis 
            competitorData={competitorData} 
            strategyData={strategyData} 
          />
        </div>
      </div>
      
      {showMultiDriverPanel && (
        <div className="multi-driver-overlay">
          <div className="multi-driver-container">
            <div className="multi-driver-header">
              <h2>Multi-Driver Management</h2>
              <button 
                className="close-button" 
                onClick={() => setShowMultiDriverPanel(false)}
              >
                ×
              </button>
            </div>
            <MultiDriverPanel />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
