import React, { useEffect, useRef, useState } from 'react';
import { Track3DRenderer } from './Track3DRenderer';
import styled from 'styled-components';

const Container = styled.div`
    width: 100%;
    height: 100%;
    position: relative;
    background: #111;
    overflow: hidden;
`;

const Overlay = styled.div`
    position: absolute;
    top: 20px;
    left: 20px;
    color: white;
    pointer-events: none;
    z-index: 10;
`;

interface Track3DVisualizationProps {
    isDarkTheme?: boolean;
}

export const Track3DVisualization: React.FC<Track3DVisualizationProps> = ({ isDarkTheme = true }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const rendererRef = useRef<Track3DRenderer | null>(null);
    const [fps, setFps] = useState(0);

    useEffect(() => {
        if (!containerRef.current) return;

        // Initialize Renderer
        const renderer = new Track3DRenderer({
            container: containerRef.current,
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight,
            isDarkTheme
        });
        rendererRef.current = renderer;

        // Handle Resize
        const handleResize = () => {
            if (containerRef.current && rendererRef.current) {
                rendererRef.current.updateDimensions(
                    containerRef.current.clientWidth,
                    containerRef.current.clientHeight
                );
            }
        };
        window.addEventListener('resize', handleResize);

        // Mock Data Loop (Temporary for testing)
        const interval = setInterval(() => {
            if (rendererRef.current) {
                // Simulate a car moving in a circle
                const time = Date.now() * 0.001;
                const x = Math.sin(time) * 20;
                const z = Math.cos(time) * 20;
                rendererRef.current.updateCarPosition('driver-1', { x, y: 1, z });
            }
        }, 16);

        // Cleanup
        return () => {
            window.removeEventListener('resize', handleResize);
            clearInterval(interval);
            if (rendererRef.current) {
                rendererRef.current.dispose();
            }
        };
    }, [isDarkTheme]);

    return (
        <Container ref={containerRef}>
            <Overlay>
                <h2>3D Track Visualization</h2>
                <p>Status: Active</p>
            </Overlay>
        </Container>
    );
};
