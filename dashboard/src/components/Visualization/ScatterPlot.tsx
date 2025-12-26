/**
 * ScatterPlot - Cosworth-style consistency and correlation analysis
 * 
 * Displays relationships over time such as:
 * - Lap time consistency (lap number vs delta to best)
 * - Sector time correlation
 * - Tire degradation over stint
 */

import React, { useRef, useEffect, useMemo } from 'react';
import './Visualization.css';

interface ScatterPoint {
    x: number;
    y: number;
    label?: string;
    highlight?: boolean;
}

interface ScatterPlotProps {
    data: ScatterPoint[];
    xLabel: string;
    yLabel: string;
    xUnit?: string;
    yUnit?: string;
    title?: string;
    showConsistencyBands?: boolean;
    targetLine?: number;  // Horizontal reference line
    width?: number;
    height?: number;
}

const ScatterPlot: React.FC<ScatterPlotProps> = ({
    data,
    xLabel,
    yLabel,
    xUnit = '',
    yUnit = '',
    title,
    showConsistencyBands = false,
    targetLine,
    width = 600,
    height = 350
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Calculate bounds
    const bounds = useMemo(() => {
        if (data.length === 0) return { minX: 0, maxX: 10, minY: -1, maxY: 1 };

        const xValues = data.map(d => d.x);
        const yValues = data.map(d => d.y);

        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);
        const minY = Math.min(...yValues);
        const maxY = Math.max(...yValues);

        const xPadding = (maxX - minX) * 0.1 || 1;
        const yPadding = (maxY - minY) * 0.15 || 0.5;

        return {
            minX: Math.floor(minX - xPadding),
            maxX: Math.ceil(maxX + xPadding),
            minY: minY - yPadding,
            maxY: maxY + yPadding
        };
    }, [data]);

    // Calculate statistics for consistency bands
    const stats = useMemo(() => {
        if (data.length < 3) return { mean: 0, stdDev: 0 };

        const yValues = data.map(d => d.y);
        const mean = yValues.reduce((sum, val) => sum + val, 0) / yValues.length;
        const variance = yValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / yValues.length;
        const stdDev = Math.sqrt(variance);

        return { mean, stdDev };
    }, [data]);

    // Draw the scatter plot
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        // Clear
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, width, height);

        // Margins
        const margin = { top: 40, right: 20, bottom: 50, left: 70 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        // Scale functions
        const scaleX = (x: number) => margin.left + ((x - bounds.minX) / (bounds.maxX - bounds.minX)) * plotWidth;
        const scaleY = (y: number) => margin.top + plotHeight - ((y - bounds.minY) / (bounds.maxY - bounds.minY)) * plotHeight;

        // Draw consistency bands
        if (showConsistencyBands && data.length >= 3) {
            // ±1 std dev band (green - consistent)
            const band1Top = scaleY(stats.mean + stats.stdDev);
            const band1Bottom = scaleY(stats.mean - stats.stdDev);
            ctx.fillStyle = 'rgba(0, 255, 136, 0.1)';
            ctx.fillRect(margin.left, band1Top, plotWidth, band1Bottom - band1Top);

            // ±2 std dev band (yellow - moderate)
            const band2Top = scaleY(stats.mean + 2 * stats.stdDev);
            const band2Bottom = scaleY(stats.mean - 2 * stats.stdDev);
            ctx.fillStyle = 'rgba(255, 200, 0, 0.05)';
            ctx.fillRect(margin.left, band2Top, plotWidth, band1Top - band2Top);
            ctx.fillRect(margin.left, band1Bottom, plotWidth, band2Bottom - band1Bottom);
        }

        // Draw grid
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.lineWidth = 1;

        for (let i = 0; i <= 5; i++) {
            const x = margin.left + (i / 5) * plotWidth;
            ctx.beginPath();
            ctx.moveTo(x, margin.top);
            ctx.lineTo(x, margin.top + plotHeight);
            ctx.stroke();

            const y = margin.top + (i / 5) * plotHeight;
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(margin.left + plotWidth, y);
            ctx.stroke();
        }

        // Draw zero line or target line
        const zeroY = targetLine !== undefined ? scaleY(targetLine) : scaleY(0);
        if (zeroY >= margin.top && zeroY <= margin.top + plotHeight) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(margin.left, zeroY);
            ctx.lineTo(margin.left + plotWidth, zeroY);
            ctx.stroke();
        }

        // Draw connecting line
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.4)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        data.forEach((point, i) => {
            const x = scaleX(point.x);
            const y = scaleY(point.y);
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();

        // Draw points
        data.forEach((point) => {
            const x = scaleX(point.x);
            const y = scaleY(point.y);

            // Determine color based on delta
            let pointColor = '#00d4ff';
            if (point.y > 0) {
                pointColor = point.y > stats.stdDev * 2 ? '#ff4444' : '#ff9900';
            } else if (point.y < 0) {
                pointColor = point.y < -stats.stdDev * 2 ? '#00ff88' : '#00cc66';
            }

            // Draw point
            ctx.beginPath();
            ctx.arc(x, y, point.highlight ? 6 : 4, 0, Math.PI * 2);
            ctx.fillStyle = point.highlight ? '#fff' : pointColor;
            ctx.fill();

            if (point.highlight) {
                ctx.strokeStyle = pointColor;
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // Draw label for highlighted points
            if (point.label && point.highlight) {
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 10px Inter, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(point.label, x, y - 10);
            }
        });

        // Draw axes
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;

        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top + plotHeight);
        ctx.lineTo(margin.left + plotWidth, margin.top + plotHeight);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top);
        ctx.lineTo(margin.left, margin.top + plotHeight);
        ctx.stroke();

        // Axis labels
        ctx.fillStyle = '#888';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';

        for (let i = 0; i <= 5; i++) {
            const val = bounds.minX + (i / 5) * (bounds.maxX - bounds.minX);
            const x = scaleX(val);
            ctx.fillText(val.toFixed(0), x, height - 15);
        }

        ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const val = bounds.minY + ((5 - i) / 5) * (bounds.maxY - bounds.minY);
            const y = margin.top + (i / 5) * plotHeight;
            ctx.fillText(val.toFixed(2), margin.left - 8, y + 4);
        }

        // Axis titles
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 13px Inter, sans-serif';
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

    }, [data, bounds, stats, width, height, showConsistencyBands, targetLine, title, xLabel, yLabel, xUnit, yUnit]);

    return (
        <div className="scatter-plot">
            <canvas
                ref={canvasRef}
                style={{ width, height }}
                className="scatter-plot__canvas"
            />
            {showConsistencyBands && (
                <div className="scatter-plot__legend">
                    <span className="scatter-plot__legend-item">
                        <span className="scatter-plot__legend-color" style={{ backgroundColor: 'rgba(0, 255, 136, 0.3)' }} />
                        ±1σ Consistent
                    </span>
                    <span className="scatter-plot__legend-item">
                        <span className="scatter-plot__legend-color" style={{ backgroundColor: 'rgba(255, 200, 0, 0.3)' }} />
                        ±2σ Moderate
                    </span>
                </div>
            )}
        </div>
    );
};

export default ScatterPlot;
