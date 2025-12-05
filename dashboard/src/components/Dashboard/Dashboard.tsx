import React, { useEffect, useState } from 'react';
import Header from '../Header/Header';
import { useAuth } from '../../context/AuthContext';
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

import { BACKEND_URL } from '../../config/environment';
import { DashboardMode } from '../Header/Header';

const Dashboard: React.FC = () => {
  // State for all dashboard data
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
  const [focusMode, setFocusMode] = useState<DashboardMode>('OVERVIEW');
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


  const [displayInfo, setDisplayInfo] = useState({
    trackName: 'Silverstone',
    sessionType: 'RACE',
    lapCount: 12
  });
  const [connected, setConnected] = useState<boolean>(false);
  const { token } = useAuth();

  // Initialize WebSocket connection
  useEffect(() => {
    // Create WebSocket service instance
    const wsService = webSocketService;

    const joinLatestSession = async () => {
      if (!token) return;
      try {
        const res = await fetch(`${BACKEND_URL}/sessions`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (data.sessions && data.sessions.length > 0) {
            const latest = data.sessions[0]; // Server sorts by created_at DESC
            console.log(`Joining session: ${latest.id} (${latest.name})`);
            wsService.joinSession(latest.id);
            setSessionInfo(prev => ({
              ...prev,
              session: 'RACE',
              track: latest.track || 'Silverstone',
              driver: latest.name || 'Sim Driver'
            }));
          }
        }
      } catch (err) {
        console.error('Failed to join session:', err);
      }
    };

    const handleConnect = () => {
      console.log('Connected to WebSocket server');
      setConnected(true);
      joinLatestSession();
    };

    const handleDisconnect = () => {
      console.log('Disconnected from WebSocket server');
      setConnected(false);
    };

    // If already connected when mounting
    if (wsService.isConnectedToServer()) {
      setConnected(true);
      joinLatestSession();
    }

    const handleTelemetryUpdate = (data: TelemetryData | TelemetryData[]) => {
      // console.log('Telemetry data received:', data); // Reduced logging
      const latest = Array.isArray(data) ? data[data.length - 1] : data;
      setTelemetryData(latest);
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

    // Subscribe to events
    const unsubscribeConnect = wsService.on('connect', handleConnect).unsubscribe;
    const unsubscribeDisconnect = wsService.on('disconnect', handleDisconnect).unsubscribe;
    const unsubscribeTelemetry = wsService.on('telemetry', handleTelemetryUpdate).unsubscribe;
    const unsubscribeCoaching = wsService.on('coaching', handleCoachingUpdate).unsubscribe;
    const unsubscribeSkillAnalysis = wsService.on('skill_analysis', handleSkillAnalysisUpdate).unsubscribe;
    const unsubscribeCompetitorData = wsService.on('competitor_data', handleCompetitorUpdate).unsubscribe;
    const unsubscribeStrategyData = wsService.on('strategy_data', handleStrategyUpdate).unsubscribe;
    const unsubscribeSessionInfo = wsService.on('session_info', handleSessionUpdate).unsubscribe;

    // Connect to WebSocket server on backend port
    wsService.connect(BACKEND_URL);

    // Clean up
    return () => {
      unsubscribeConnect();
      unsubscribeDisconnect();
      unsubscribeTelemetry();
      unsubscribeCoaching();
      unsubscribeSkillAnalysis();
      unsubscribeCompetitorData();
      unsubscribeStrategyData();
      unsubscribeSessionInfo();
      // Do not disconnect service as it might be shared, but here it's fine
      // wsService.disconnect(); 
    };
  }, [token]);

  const renderDashboardContent = () => {
    switch (focusMode) {
      case 'FOCUS':
        return (
          <>
            <div className="dashboard-column full-width">
              <div className="dashboard-row">
                <Telemetry telemetryData={telemetryData} />
                <VideoPanel driverCamActive={true} spotterCamActive={true} />
              </div>
              <div className="dashboard-row secondary">
                <AICoaching insights={coachingInsights?.slice(0, 2) || null} skillAnalysis={null} />
              </div>
            </div>
          </>
        );
      case 'ENGINEER':
        return (
          <>
            <div className="dashboard-left">
              <Telemetry telemetryData={telemetryData} />
              <AICoaching insights={coachingInsights} skillAnalysis={skillAnalysis} />
            </div>
            <div className="dashboard-right wide">
              <VideoPanel driverCamActive={true} spotterCamActive={true} />
              <TrackMap telemetryData={telemetryData} trackName={sessionInfo.track || 'Unknown Track'} />
            </div>
          </>
        );
      case 'STRATEGY':
        return (
          <>
            <div className="dashboard-left">
              <TrackMap telemetryData={telemetryData} trackName={sessionInfo.track || 'Unknown Track'} />
              <CompetitorPositions competitorData={competitorData} />
            </div>
            <div className="dashboard-center wide">
              <CompetitorAnalysis competitorData={competitorData} strategyData={strategyData} />
            </div>
          </>
        );
      case 'OVERVIEW':
      default:
        return (
          <>
            <div className="dashboard-left">
              <Telemetry telemetryData={telemetryData} />
              <TrackMap telemetryData={telemetryData} trackName={sessionInfo.track || 'Unknown Track'} />
            </div>

            <div className="dashboard-center">
              <AICoaching insights={coachingInsights} skillAnalysis={skillAnalysis} />
              <VideoPanel driverCamActive={true} spotterCamActive={true} />
            </div>

            <div className="dashboard-right">
              <CompetitorPositions competitorData={competitorData} />
              <CompetitorAnalysis competitorData={competitorData} strategyData={strategyData} />
            </div>
          </>
        );
    }
  };

  return (
    <div className={`dashboard mode-${focusMode.toLowerCase()}`}>
      <Header
        connected={connected}
        currentMode={focusMode}
        onModeChange={setFocusMode}
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
        {renderDashboardContent()}
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
