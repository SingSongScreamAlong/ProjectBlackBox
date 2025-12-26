/**
 * MultiStreamGrid - Grid of multiple driver streams
 * 
 * Phase 2 component for viewing multiple streams simultaneously
 * with ability to focus on one while keeping others visible.
 */

import React, { useState, useMemo } from 'react';
import StreamPlayer from './StreamPlayer';
import './MultiStreamGrid.css';

interface StreamSource {
    streamId: string;
    driverId: string;
    driverName: string;
    carNumber: string;
    position: number;
    status: 'live' | 'offline' | 'degraded';
}

interface MultiStreamGridProps {
    streams: StreamSource[];
    socket?: any;
    maxVisible?: number;
    onStreamFocus?: (streamId: string) => void;
}

const MultiStreamGrid: React.FC<MultiStreamGridProps> = ({
    streams,
    socket,
    maxVisible = 4,
    onStreamFocus,
}) => {
    const [focusedStreamId, setFocusedStreamId] = useState<string | null>(null);
    const [layout, setLayout] = useState<'grid' | '1+3' | 'focused'>('grid');

    // Sort streams by position
    const sortedStreams = useMemo(() => {
        return [...streams]
            .filter(s => s.status !== 'offline')
            .sort((a, b) => a.position - b.position)
            .slice(0, maxVisible);
    }, [streams, maxVisible]);

    const focusedStream = focusedStreamId
        ? sortedStreams.find(s => s.streamId === focusedStreamId)
        : null;

    const otherStreams = focusedStreamId
        ? sortedStreams.filter(s => s.streamId !== focusedStreamId)
        : sortedStreams;

    const handleStreamClick = (streamId: string) => {
        if (layout === 'grid') {
            setFocusedStreamId(streamId);
            setLayout('1+3');
        } else if (focusedStreamId === streamId) {
            setFocusedStreamId(null);
            setLayout('grid');
        } else {
            setFocusedStreamId(streamId);
        }
        onStreamFocus?.(streamId);
    };

    const getGridColumns = () => {
        switch (layout) {
            case 'focused':
                return 1;
            case '1+3':
                return focusedStream ? 1 : 2;
            default:
                return sortedStreams.length <= 2 ? sortedStreams.length : 2;
        }
    };

    if (sortedStreams.length === 0) {
        return (
            <div className="multi-stream-grid multi-stream-grid--empty">
                <p>No live streams available</p>
            </div>
        );
    }

    return (
        <div className="multi-stream-grid">
            <div className="multi-stream-grid__controls">
                <button
                    className={layout === 'grid' ? 'active' : ''}
                    onClick={() => { setLayout('grid'); setFocusedStreamId(null); }}
                >
                    Grid
                </button>
                <button
                    className={layout === '1+3' ? 'active' : ''}
                    onClick={() => setLayout('1+3')}
                    disabled={!focusedStreamId}
                >
                    1+3
                </button>
                <button
                    className={layout === 'focused' ? 'active' : ''}
                    onClick={() => setLayout('focused')}
                    disabled={!focusedStreamId}
                >
                    Focus
                </button>
            </div>

            <div
                className={`multi-stream-grid__container layout--${layout}`}
                style={{ '--grid-cols': getGridColumns() } as React.CSSProperties}
            >
                {/* Focused stream (large) */}
                {focusedStream && layout !== 'grid' && (
                    <div
                        className="multi-stream-grid__focused"
                        onClick={() => handleStreamClick(focusedStream.streamId)}
                    >
                        <StreamPlayer
                            streamId={focusedStream.streamId}
                            socket={socket}
                            quality="high"
                        />
                        <div className="multi-stream-grid__label">
                            <span className="position">P{focusedStream.position}</span>
                            <span className="driver">#{focusedStream.carNumber} {focusedStream.driverName}</span>
                        </div>
                    </div>
                )}

                {/* Other streams (small or equal) */}
                <div className={`multi-stream-grid__others ${layout !== 'grid' ? 'sidebar' : ''}`}>
                    {(layout === 'grid' ? sortedStreams : otherStreams).map(stream => (
                        <div
                            key={stream.streamId}
                            className="multi-stream-grid__cell"
                            onClick={() => handleStreamClick(stream.streamId)}
                        >
                            <StreamPlayer
                                streamId={stream.streamId}
                                socket={socket}
                                quality={layout === 'grid' ? 'med' : 'low'}
                            />
                            <div className="multi-stream-grid__label">
                                <span className="position">P{stream.position}</span>
                                <span className="driver">#{stream.carNumber} {stream.driverName}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default MultiStreamGrid;
