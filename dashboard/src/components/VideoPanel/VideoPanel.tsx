import React, { useState, useEffect, useRef } from 'react';
import WebSocketService from '../../services/WebSocketService';

interface VideoPanelProps {
  driverCamActive?: boolean;
}

const VideoPanel: React.FC<VideoPanelProps> = ({
  driverCamActive = true
}) => {
  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const frameCountRef = useRef(0);
  const lastFrameTimeRef = useRef(Date.now());
  const [fps, setFps] = useState(0);

  useEffect(() => {
    // Subscribe to video frames
    const handleVideoFrame = (base64Image: string) => {
      // Simple FPS counter
      frameCountRef.current++;
      const now = Date.now();
      if (now - lastFrameTimeRef.current >= 1000) {
        setFps(frameCountRef.current);
        frameCountRef.current = 0;
        lastFrameTimeRef.current = now;
      }

      // Update image source
      setVideoSrc(`data:image/jpeg;base64,${base64Image}`);
    };

    // Use the onVideoData method from the service
    const subscription = WebSocketService.onVideoData(handleVideoFrame);

    return () => {
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
