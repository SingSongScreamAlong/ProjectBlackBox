/**
 * SponsorExposure - Track and display sponsor visibility metrics
 * 
 * Provides analytics on sponsor logo visibility during broadcasts,
 * including total screen time, exposure by session, and exportable reports.
 */

import React, { useState, useEffect, useCallback } from 'react';
import './SponsorExposure.css';

interface Sponsor {
    id: string;
    name: string;
    logoUrl: string;
    tier: 'title' | 'major' | 'associate' | 'partner';
    placement: string[];  // e.g., ['car_livery', 'helmet', 'suit', 'pit_wall']
}

interface ExposureEvent {
    sponsorId: string;
    sessionId: string;
    timestamp: number;
    durationMs: number;
    placement: string;
    visibilityPct: number;  // 0-100, how much of logo was visible
}

interface SponsorStats {
    sponsor: Sponsor;
    totalExposureMs: number;
    sessionCount: number;
    avgVisibility: number;
    peakViewers: number;
    estimatedImpressions: number;
}

interface SponsorExposureProps {
    teamId: string;
    sessionId?: string;  // Optional: filter to specific session
    onExport?: (data: SponsorStats[]) => void;
}

const SponsorExposure: React.FC<SponsorExposureProps> = ({
    teamId,
    sessionId,
    onExport
}) => {
    const [sponsors, setSponsors] = useState<Sponsor[]>([]);
    const [stats, setStats] = useState<SponsorStats[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [timeRange, setTimeRange] = useState<'session' | 'week' | 'month' | 'all'>('session');
    const [sortBy, setSortBy] = useState<'exposure' | 'impressions' | 'visibility'>('exposure');

    // Fetch sponsor data
    const fetchSponsors = useCallback(async () => {
        try {
            setLoading(true);
            const response = await fetch(`/api/teams/${teamId}/sponsors`);

            if (!response.ok) {
                throw new Error('Failed to fetch sponsors');
            }

            const data = await response.json();
            setSponsors(data.sponsors || []);

            // Calculate stats for each sponsor
            const sponsorStats: SponsorStats[] = (data.sponsors || []).map((sponsor: Sponsor) => ({
                sponsor,
                totalExposureMs: data.exposure?.[sponsor.id]?.totalMs || 0,
                sessionCount: data.exposure?.[sponsor.id]?.sessions || 0,
                avgVisibility: data.exposure?.[sponsor.id]?.avgVisibility || 0,
                peakViewers: data.exposure?.[sponsor.id]?.peakViewers || 0,
                estimatedImpressions: data.exposure?.[sponsor.id]?.impressions || 0,
            }));

            setStats(sponsorStats);
            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load sponsor data');
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => {
        fetchSponsors();
    }, [fetchSponsors, timeRange]);

    // Format duration for display
    const formatDuration = (ms: number): string => {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        }
        return `${seconds}s`;
    };

    // Format large numbers
    const formatNumber = (num: number): string => {
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(1)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(1)}K`;
        }
        return num.toString();
    };

    // Sort stats based on selected criteria
    const sortedStats = [...stats].sort((a, b) => {
        switch (sortBy) {
            case 'exposure':
                return b.totalExposureMs - a.totalExposureMs;
            case 'impressions':
                return b.estimatedImpressions - a.estimatedImpressions;
            case 'visibility':
                return b.avgVisibility - a.avgVisibility;
            default:
                return 0;
        }
    });

    // Get tier color
    const getTierColor = (tier: Sponsor['tier']): string => {
        switch (tier) {
            case 'title': return '#ffd700';
            case 'major': return '#c0c0c0';
            case 'associate': return '#cd7f32';
            case 'partner': return '#00d4ff';
        }
    };

    // Handle export
    const handleExport = () => {
        if (onExport) {
            onExport(sortedStats);
        } else {
            // Default: download as CSV
            const csv = [
                ['Sponsor', 'Tier', 'Total Exposure', 'Sessions', 'Avg Visibility %', 'Peak Viewers', 'Est. Impressions'],
                ...sortedStats.map(s => [
                    s.sponsor.name,
                    s.sponsor.tier,
                    formatDuration(s.totalExposureMs),
                    s.sessionCount,
                    s.avgVisibility.toFixed(1),
                    s.peakViewers,
                    s.estimatedImpressions
                ])
            ].map(row => row.join(',')).join('\n');

            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sponsor-exposure-${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        }
    };

    if (loading) {
        return (
            <div className="sponsor-exposure sponsor-exposure--loading">
                <div className="sponsor-exposure__spinner" />
                <p>Loading sponsor data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="sponsor-exposure sponsor-exposure--error">
                <h3>⚠️ Error</h3>
                <p>{error}</p>
                <button onClick={fetchSponsors}>Retry</button>
            </div>
        );
    }

    return (
        <div className="sponsor-exposure">
            <header className="sponsor-exposure__header">
                <h2>📊 Sponsor Exposure Analytics</h2>
                <div className="sponsor-exposure__controls">
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
                        className="sponsor-exposure__select"
                    >
                        <option value="session">This Session</option>
                        <option value="week">Past 7 Days</option>
                        <option value="month">Past 30 Days</option>
                        <option value="all">All Time</option>
                    </select>

                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                        className="sponsor-exposure__select"
                    >
                        <option value="exposure">Sort by Exposure</option>
                        <option value="impressions">Sort by Impressions</option>
                        <option value="visibility">Sort by Visibility</option>
                    </select>

                    <button
                        className="sponsor-exposure__export-btn"
                        onClick={handleExport}
                    >
                        📥 Export Report
                    </button>
                </div>
            </header>

            <div className="sponsor-exposure__summary">
                <div className="sponsor-exposure__stat-card">
                    <span className="sponsor-exposure__stat-value">
                        {formatDuration(stats.reduce((sum, s) => sum + s.totalExposureMs, 0))}
                    </span>
                    <span className="sponsor-exposure__stat-label">Total Exposure</span>
                </div>
                <div className="sponsor-exposure__stat-card">
                    <span className="sponsor-exposure__stat-value">
                        {formatNumber(stats.reduce((sum, s) => sum + s.estimatedImpressions, 0))}
                    </span>
                    <span className="sponsor-exposure__stat-label">Est. Impressions</span>
                </div>
                <div className="sponsor-exposure__stat-card">
                    <span className="sponsor-exposure__stat-value">
                        {Math.max(...stats.map(s => s.peakViewers), 0)}
                    </span>
                    <span className="sponsor-exposure__stat-label">Peak Viewers</span>
                </div>
            </div>

            <div className="sponsor-exposure__list">
                {sortedStats.length === 0 ? (
                    <p className="sponsor-exposure__empty">No sponsors registered for this team.</p>
                ) : (
                    sortedStats.map((stat) => (
                        <div
                            key={stat.sponsor.id}
                            className="sponsor-exposure__card"
                            style={{ borderLeftColor: getTierColor(stat.sponsor.tier) }}
                        >
                            <div className="sponsor-exposure__card-header">
                                <div className="sponsor-exposure__sponsor-info">
                                    {stat.sponsor.logoUrl && (
                                        <img
                                            src={stat.sponsor.logoUrl}
                                            alt={stat.sponsor.name}
                                            className="sponsor-exposure__logo"
                                        />
                                    )}
                                    <div>
                                        <h3 className="sponsor-exposure__sponsor-name">{stat.sponsor.name}</h3>
                                        <span
                                            className="sponsor-exposure__tier"
                                            style={{ color: getTierColor(stat.sponsor.tier) }}
                                        >
                                            {stat.sponsor.tier.toUpperCase()} SPONSOR
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="sponsor-exposure__card-stats">
                                <div className="sponsor-exposure__metric">
                                    <span className="sponsor-exposure__metric-value">
                                        {formatDuration(stat.totalExposureMs)}
                                    </span>
                                    <span className="sponsor-exposure__metric-label">Screen Time</span>
                                </div>
                                <div className="sponsor-exposure__metric">
                                    <span className="sponsor-exposure__metric-value">
                                        {stat.avgVisibility.toFixed(0)}%
                                    </span>
                                    <span className="sponsor-exposure__metric-label">Avg Visibility</span>
                                </div>
                                <div className="sponsor-exposure__metric">
                                    <span className="sponsor-exposure__metric-value">
                                        {formatNumber(stat.estimatedImpressions)}
                                    </span>
                                    <span className="sponsor-exposure__metric-label">Impressions</span>
                                </div>
                                <div className="sponsor-exposure__metric">
                                    <span className="sponsor-exposure__metric-value">
                                        {stat.sessionCount}
                                    </span>
                                    <span className="sponsor-exposure__metric-label">Sessions</span>
                                </div>
                            </div>

                            <div className="sponsor-exposure__placements">
                                {stat.sponsor.placement.map(p => (
                                    <span key={p} className="sponsor-exposure__placement-tag">
                                        {p.replace('_', ' ')}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default SponsorExposure;
