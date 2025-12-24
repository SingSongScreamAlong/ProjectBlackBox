import React, { useState, useEffect } from 'react';
import WebSocketService from '../../services/WebSocketService';

interface VideoPanelProps {
  driverCamActive?: boolean;
}

const VideoPanel: React.FC<VideoPanelProps> = ({
  driverCamActive = true
}) => {
  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const [fps, setFps] = useState(0);

  useEffect(() => {
    console.log('📹 VideoPanel: Subscribing to video_data events');

    // Rolling FPS tracker (stores last 30 frame timestamps)
    const frameTimestamps: number[] = [];
    const MAX_SAMPLES = 30;

    // Subscribe to video frames
    const handleVideoFrame = (base64Image: string) => {
      const now = performance.now();

      // Add timestamp and remove old ones
      frameTimestamps.push(now);
      while (frameTimestamps.length > MAX_SAMPLES) {
        frameTimestamps.shift();
      }

      // Calculate rolling FPS from timestamps
      if (frameTimestamps.length >= 2) {
        const oldestTime = frameTimestamps[0];
        const timeSpan = (now - oldestTime) / 1000; // in seconds
        if (timeSpan > 0) {
          const rollingFps = Math.round((frameTimestamps.length - 1) / timeSpan);
          setFps(rollingFps);
        }
      }

      // Update image source using requestAnimationFrame for smooth rendering
      requestAnimationFrame(() => {
        setVideoSrc(`data:image/jpeg;base64,${base64Image}`);
      });
    };

    // Use the onVideoData method from the service
    const subscription = WebSocketService.onVideoData(handleVideoFrame);
    console.log('📹 VideoPanel: Subscription active');

    return () => {
      console.log('📹 VideoPanel: Unsubscribing from video_data events');
      subscription.unsubscribe();
    };
  }, []);

  return (
    <div className="video-panel">
      {/* Driver Camera Feed */}
      <div className="panel">
        <div className="panel-header">DRIVER CAM</div>
        <div className="video-container">
          <div className="video-feed">
            {videoSrc ? (
              <img
                src={videoSrc}
                alt="Driver Cam"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ fontSize: '32px', marginBottom: '8px' }}>📹</div>
                <div style={{ color: '#ff8c00', fontWeight: '600' }}>
                  {driverCamActive ? '⏱️ No Video Feed' : 'DRIVER CAM OFFLINE'}
                </div>
                <div style={{ fontSize: '12px', color: '#7d8590', marginTop: '4px' }}>
                  COCKPIT VIEW • 1920x1080
                </div>
              </div>
            )}

            <div className="video-overlay"></div>
            <div className="video-info">
              <div className="video-status">
                {driverCamActive && videoSrc && <div className="live-indicator"></div>}
                <span>DRIVER CAM</span>
              </div>
              <div className="video-quality">{fps > 0 ? `${fps}fps` : '--'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPanel;
