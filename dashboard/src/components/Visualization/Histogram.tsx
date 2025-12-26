/**
 * Histogram - Cosworth-style frequency distribution chart
 * 
 * Displays distribution of telemetry values such as:
 * - Gear usage distribution
 * - Brake point distribution by corner
 * - Speed distribution
 */

import React, { useRef, useEffect, useMemo } from 'react';
import './Visualization.css';

interface HistogramProps {
    data: number[];
    bins?: number;
    label: string;
    unit?: string;
    title?: string;
    color?: string;
    showMean?: boolean;
    showMedian?: boolean;
    width?: number;
    height?: number;
}

const Histogram: React.FC<HistogramProps> = ({
    data,
    bins = 20,
    label,
    unit = '',
    title,
    color = '#00d4ff',
    showMean = true,
    showMedian = false,
    width = 600,
    height = 300
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Calculate histogram bins
    const histogram = useMemo(() => {
        if (data.length === 0) return { bins: [], min: 0, max: 100, binWidth: 1 };

        const min = Math.min(...data);
        const max = Math.max(...data);
        const range = max - min || 1;
        const binWidth = range / bins;

        const binCounts = new Array(bins).fill(0);

        data.forEach(value => {
            let binIndex = Math.floor((value - min) / binWidth);
            if (binIndex >= bins) binIndex = bins - 1;
            if (binIndex < 0) binIndex = 0;
            binCounts[binIndex]++;
        });

        return { bins: binCounts, min, max, binWidth };
    }, [data, bins]);

    // Calculate statistics
    const stats = useMemo(() => {
        if (data.length === 0) return { mean: 0, median: 0 };

        const sorted = [...data].sort((a, b) => a - b);
        const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
        const median = sorted.length % 2 === 0
            ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
            : sorted[Math.floor(sorted.length / 2)];

        return { mean, median };
    }, [data]);

    // Draw the histogram
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
        const margin = { top: 40, right: 20, bottom: 50, left: 60 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        const maxCount = Math.max(...histogram.bins, 1);
        const barWidth = plotWidth / histogram.bins.length;

        // Draw bars
        histogram.bins.forEach((count, i) => {
            const x = margin.left + i * barWidth;
            const barHeight = (count / maxCount) * plotHeight;
            const y = margin.top + plotHeight - barHeight;

            // Bar gradient
            const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
            gradient.addColorStop(0, color);
            gradient.addColorStop(1, `${color}66`);

            ctx.fillStyle = gradient;
            ctx.fillRect(x + 1, y, barWidth - 2, barHeight);

            // Bar border
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;
            ctx.strokeRect(x + 1, y, barWidth - 2, barHeight);
        });

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
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';

        // X axis labels (5 labels)
        for (let i = 0; i <= 4; i++) {
            const val = histogram.min + (i / 4) * (histogram.max - histogram.min);
            const x = margin.left + (i / 4) * plotWidth;
            ctx.fillText(val.toFixed(1), x, height - 15);
        }

        // Y axis labels
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {
            const count = Math.round((i / 4) * maxCount);
            const y = margin.top + plotHeight - (i / 4) * plotHeight;
            ctx.fillText(count.toString(), margin.left - 8, y + 4);
        }

        // Draw mean line
        if (showMean && data.length > 0) {
            const meanX = margin.left + ((stats.mean - histogram.min) / (histogram.max - histogram.min)) * plotWidth;

            ctx.strokeStyle = '#ff9900';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(meanX, margin.top);
            ctx.lineTo(meanX, margin.top + plotHeight);
            ctx.stroke();
            ctx.setLineDash([]);

            // Mean label
            ctx.fillStyle = '#ff9900';
            ctx.font = 'bold 11px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`μ = ${stats.mean.toFixed(2)}`, meanX, margin.top - 5);
        }

        // Draw median line
        if (showMedian && data.length > 0) {
            const medianX = margin.left + ((stats.median - histogram.min) / (histogram.max - histogram.min)) * plotWidth;

            ctx.strokeStyle = '#00ff88';
            ctx.lineWidth = 2;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(medianX, margin.top);
            ctx.lineTo(medianX, margin.top + plotHeight);
            ctx.stroke();
            ctx.setLineDash([]);

            // Median label
            ctx.fillStyle = '#00ff88';
            ctx.font = 'bold 11px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`M = ${stats.median.toFixed(2)}`, medianX, margin.top - 15);
        }

        // Axis titles
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 13px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${label}${unit ? ` (${unit})` : ''}`, width / 2, height - 5);

        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Frequency', 0, 0);
        ctx.restore();

        // Draw title
        if (title) {
            ctx.font = 'bold 16px Inter, sans-serif';
            ctx.fillStyle = '#00d4ff';
            ctx.textAlign = 'center';
            ctx.fillText(title, width / 2, 25);
        }

    }, [histogram, stats, data, width, height, color, showMean, showMedian, title, label, unit]);

    return (
        <div className="histogram">
            <canvas
                ref={canvasRef}
                style={{ width, height }}
                className="histogram__canvas"
            />
            <div className="histogram__stats">
                <span>n = {data.length}</span>
                {showMean && <span style={{ color: '#ff9900' }}>Mean: {stats.mean.toFixed(2)}</span>}
                {showMedian && <span style={{ color: '#00ff88' }}>Median: {stats.median.toFixed(2)}</span>}
            </div>
        </div>
    );
};

export default Histogram;
