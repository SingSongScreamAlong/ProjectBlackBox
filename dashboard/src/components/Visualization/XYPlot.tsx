/**
 * XYPlot - Cosworth-style XY scatter visualization
 * 
 * Displays relationships between telemetry variables such as:
 * - Lateral G vs Speed
 * - Throttle vs Brake
 * - Steering angle vs Speed
 */

import React, { useRef, useEffect, useMemo } from 'react';
import './Visualization.css';

interface DataPoint {
    x: number;
    y: number;
    lap?: number;
    timestamp?: number;
}

interface XYPlotProps {
    data: DataPoint[];
    xLabel: string;
    yLabel: string;
    xUnit?: string;
    yUnit?: string;
    title?: string;
    colorByLap?: boolean;
    showGrid?: boolean;
    showTrendLine?: boolean;
    width?: number;
    height?: number;
}

const XYPlot: React.FC<XYPlotProps> = ({
    data,
    xLabel,
    yLabel,
    xUnit = '',
    yUnit = '',
    title,
    colorByLap = false,
    showGrid = true,
    showTrendLine = false,
    width = 600,
    height = 400
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Calculate bounds with padding
    const bounds = useMemo(() => {
        if (data.length === 0) return { minX: 0, maxX: 100, minY: 0, maxY: 100 };

        const xValues = data.map(d => d.x);
        const yValues = data.map(d => d.y);

        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);
        const minY = Math.min(...yValues);
        const maxY = Math.max(...yValues);

        // Add 10% padding
        const xPadding = (maxX - minX) * 0.1 || 10;
        const yPadding = (maxY - minY) * 0.1 || 10;

        return {
            minX: minX - xPadding,
            maxX: maxX + xPadding,
            minY: minY - yPadding,
            maxY: maxY + yPadding
        };
    }, [data]);

    // Get unique laps for coloring
    const uniqueLaps = useMemo(() => {
        return [...new Set(data.map(d => d.lap).filter(Boolean))].sort((a, b) => (a || 0) - (b || 0));
    }, [data]);

    // Generate lap color
    const getLapColor = (lap: number | undefined): string => {
        if (!lap || !colorByLap) return 'rgba(0, 212, 255, 0.6)';
        const lapIndex = uniqueLaps.indexOf(lap);
        const hue = (lapIndex * 137.5) % 360; // Golden angle for good color distribution
        return `hsla(${hue}, 70%, 60%, 0.6)`;
    };

    // Draw the plot
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set up high DPI rendering
        const dpr = window.devicePixelRatio || 1;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        // Clear canvas
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, width, height);

        // Margins for labels
        const margin = { top: 40, right: 20, bottom: 50, left: 60 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        // Scale functions
        const scaleX = (x: number) => margin.left + ((x - bounds.minX) / (bounds.maxX - bounds.minX)) * plotWidth;
        const scaleY = (y: number) => margin.top + plotHeight - ((y - bounds.minY) / (bounds.maxY - bounds.minY)) * plotHeight;

        // Draw grid
        if (showGrid) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.lineWidth = 1;

            // Vertical grid lines
            const xSteps = 5;
            for (let i = 0; i <= xSteps; i++) {
                const x = margin.left + (i / xSteps) * plotWidth;
                ctx.beginPath();
                ctx.moveTo(x, margin.top);
                ctx.lineTo(x, margin.top + plotHeight);
                ctx.stroke();
            }

            // Horizontal grid lines
            const ySteps = 5;
            for (let i = 0; i <= ySteps; i++) {
                const y = margin.top + (i / ySteps) * plotHeight;
                ctx.beginPath();
                ctx.moveTo(margin.left, y);
                ctx.lineTo(margin.left + plotWidth, y);
                ctx.stroke();
            }
        }

        // Draw axes
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;

        // X axis
        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top + plotHeight);
        ctx.lineTo(margin.left + plotWidth, margin.top + plotHeight);
        ctx.stroke();

        // Y axis
        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top);
        ctx.lineTo(margin.left, margin.top + plotHeight);
        ctx.stroke();

        // Axis labels
        ctx.fillStyle = '#888';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';

        // X axis labels
        for (let i = 0; i <= 5; i++) {
            const val = bounds.minX + (i / 5) * (bounds.maxX - bounds.minX);
            const x = scaleX(val);
            ctx.fillText(val.toFixed(1), x, height - 10);
        }

        // Y axis labels
        ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const val = bounds.minY + (i / 5) * (bounds.maxY - bounds.minY);
            const y = scaleY(val);
            ctx.fillText(val.toFixed(1), margin.left - 8, y + 4);
        }

        // Axis titles
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${xLabel}${xUnit ? ` (${xUnit})` : ''}`, width / 2, height - 5);

        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(`${yLabel}${yUnit ? ` (${yUnit})` : ''}`, 0, 0);
        ctx.restore();

        // Draw title
        if (title) {
            ctx.font = 'bold 16px Inter, sans-serif';
            ctx.fillStyle = '#00d4ff';
            ctx.textAlign = 'center';
            ctx.fillText(title, width / 2, 25);
        }

        // Draw data points
        data.forEach(point => {
            const x = scaleX(point.x);
            const y = scaleY(point.y);

            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = getLapColor(point.lap);
            ctx.fill();
        });

        // Draw trend line if enabled
        if (showTrendLine && data.length > 1) {
            // Simple linear regression
            const n = data.length;
            const sumX = data.reduce((sum, d) => sum + d.x, 0);
            const sumY = data.reduce((sum, d) => sum + d.y, 0);
            const sumXY = data.reduce((sum, d) => sum + d.x * d.y, 0);
            const sumXX = data.reduce((sum, d) => sum + d.x * d.x, 0);

            const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
            const intercept = (sumY - slope * sumX) / n;

            ctx.strokeStyle = 'rgba(255, 153, 0, 0.8)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(scaleX(bounds.minX), scaleY(slope * bounds.minX + intercept));
            ctx.lineTo(scaleX(bounds.maxX), scaleY(slope * bounds.maxX + intercept));
            ctx.stroke();
            ctx.setLineDash([]);
        }

    }, [data, bounds, width, height, showGrid, showTrendLine, title, xLabel, yLabel, xUnit, yUnit, colorByLap, uniqueLaps]);

    return (
        <div className="xy-plot">
            <canvas
                ref={canvasRef}
                style={{ width, height }}
                className="xy-plot__canvas"
            />
            {colorByLap && uniqueLaps.length > 0 && (
                <div className="xy-plot__legend">
                    {uniqueLaps.slice(0, 10).map(lap => (
                        <div key={lap} className="xy-plot__legend-item">
                            <span
                                className="xy-plot__legend-color"
                                style={{ backgroundColor: getLapColor(lap) }}
                            />
                            <span>Lap {lap}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default XYPlot;
