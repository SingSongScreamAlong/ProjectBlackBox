import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';

export interface TrackPoint {
  x: number;
  y: number;
  distance: number;
  sectorIndex?: number;
}

export interface DriverMapPosition {
  driverId: string;
  driverName: string;
  driverNumber: string;
  position: number;
  teamColor: string;
  x: number;
  y: number;
  distance: number;
  speed: number;
}

interface TrackMapGeneratorProps {
  trackData: TrackPoint[];
  drivers: DriverMapPosition[];
  width?: number;
  height?: number;
  showSectors?: boolean;
  showDriverNumbers?: boolean;
  highlightedDriverId?: string;
  className?: string;
}

export const TrackMapGenerator: React.FC<TrackMapGeneratorProps> = ({
  trackData,
  drivers,
  width = 600,
  height = 400,
  showSectors = true,
  showDriverNumbers = true,
  highlightedDriverId,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Normalize track coordinates to fit canvas
  const normalizedTrack = useMemo(() => {
    if (trackData.length === 0) return [];

    const xValues = trackData.map((p) => p.x);
    const yValues = trackData.map((p) => p.y);

    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);

    const xRange = xMax - xMin;
    const yRange = yMax - yMin;

    const padding = 40;
    const scale = Math.min(
      (width - 2 * padding) / xRange,
      (height - 2 * padding) / yRange
    );

    return trackData.map((point) => ({
      ...point,
      x: (point.x - xMin) * scale + padding,
      y: (point.y - yMin) * scale + padding,
    }));
  }, [trackData, width, height]);

  // Normalize driver positions
  const normalizedDrivers = useMemo(() => {
    if (trackData.length === 0 || drivers.length === 0) return [];

    const xValues = trackData.map((p) => p.x);
    const yValues = trackData.map((p) => p.y);

    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);

    const xRange = xMax - xMin;
    const yRange = yMax - yMin;

    const padding = 40;
    const scale = Math.min(
      (width - 2 * padding) / xRange,
      (height - 2 * padding) / yRange
    );

    return drivers.map((driver) => ({
      ...driver,
      x: (driver.x - xMin) * scale + padding,
      y: (driver.y - yMin) * scale + padding,
    }));
  }, [trackData, drivers, width, height]);

  useEffect(() => {
    if (!svgRef.current || normalizedTrack.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Create line generator
    const lineGenerator = d3
      .line<TrackPoint>()
      .x((d) => d.x)
      .y((d) => d.y)
      .curve(d3.curveCatmullRom.alpha(0.5));

    // Group track points by sector
    const sectorGroups = d3.group(normalizedTrack, (d) => d.sectorIndex ?? 0);

    // Draw track with sector colors
    if (showSectors && sectorGroups.size > 1) {
      const sectorColors = ['#22c55e', '#eab308', '#9333ea'];

      sectorGroups.forEach((points, sectorIndex) => {
        // Draw track segment
        svg
          .append('path')
          .datum(points)
          .attr('d', lineGenerator)
          .attr('fill', 'none')
          .attr('stroke', sectorColors[sectorIndex % sectorColors.length])
          .attr('stroke-width', 8)
          .attr('stroke-linecap', 'round')
          .attr('stroke-linejoin', 'round')
          .attr('opacity', 0.8);

        // Draw track outline
        svg
          .append('path')
          .datum(points)
          .attr('d', lineGenerator)
          .attr('fill', 'none')
          .attr('stroke', 'rgba(255, 255, 255, 0.3)')
          .attr('stroke-width', 12)
          .attr('stroke-linecap', 'round')
          .attr('stroke-linejoin', 'round')
          .attr('opacity', 0.3);
      });
    } else {
      // Draw single track line
      svg
        .append('path')
        .datum(normalizedTrack)
        .attr('d', lineGenerator)
        .attr('fill', 'none')
        .attr('stroke', 'rgba(255, 255, 255, 0.3)')
        .attr('stroke-width', 12)
        .attr('stroke-linecap', 'round')
        .attr('stroke-linejoin', 'round');

      svg
        .append('path')
        .datum(normalizedTrack)
        .attr('d', lineGenerator)
        .attr('fill', 'none')
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 8)
        .attr('stroke-linecap', 'round')
        .attr('stroke-linejoin', 'round')
        .attr('opacity', 0.8);
    }

    // Draw start/finish line
    if (normalizedTrack.length > 0) {
      const startPoint = normalizedTrack[0];

      svg
        .append('line')
        .attr('x1', startPoint.x - 10)
        .attr('y1', startPoint.y)
        .attr('x2', startPoint.x + 10)
        .attr('y2', startPoint.y)
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 4)
        .attr('stroke-linecap', 'round');

      svg
        .append('text')
        .attr('x', startPoint.x)
        .attr('y', startPoint.y - 15)
        .attr('text-anchor', 'middle')
        .attr('fill', '#ffffff')
        .attr('font-size', '12px')
        .attr('font-weight', 700)
        .text('START/FINISH');
    }

    // Draw drivers
    const driverGroups = svg
      .selectAll('.driver')
      .data(normalizedDrivers)
      .enter()
      .append('g')
      .attr('class', 'driver')
      .attr('transform', (d) => `translate(${d.x}, ${d.y})`);

    // Driver circles
    driverGroups
      .append('circle')
      .attr('r', (d) => (highlightedDriverId === d.driverId ? 8 : 6))
      .attr('fill', (d) => d.teamColor)
      .attr('stroke', (d) =>
        highlightedDriverId === d.driverId ? '#ffffff' : 'rgba(0, 0, 0, 0.5)'
      )
      .attr('stroke-width', (d) => (highlightedDriverId === d.driverId ? 2 : 1))
      .attr('opacity', 1)
      .style('cursor', 'pointer');

    // Driver numbers
    if (showDriverNumbers) {
      driverGroups
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', '#ffffff')
        .attr('font-size', '8px')
        .attr('font-weight', 700)
        .text((d) => d.driverNumber);
    }

    // Tooltips
    driverGroups
      .append('title')
      .text(
        (d) =>
          `P${d.position} - ${d.driverName}\n${Math.round(d.speed)} km/h\nDistance: ${Math.round(d.distance)}m`
      );
  }, [
    normalizedTrack,
    normalizedDrivers,
    showSectors,
    showDriverNumbers,
    highlightedDriverId,
  ]);

  return (
    <div
      ref={containerRef}
      className={`track-map-generator ${className}`}
      style={{
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(20px)',
        borderRadius: '12px',
        padding: '16px',
        width: '100%',
        height: '100%',
      }}
    >
      {/* Header */}
      <div
        style={{
          marginBottom: '12px',
          paddingBottom: '12px',
          borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <h2
          style={{
            color: 'white',
            fontSize: '18px',
            fontWeight: 700,
            letterSpacing: '1px',
            margin: 0,
          }}
        >
          TRACK MAP
        </h2>
        {showSectors && (
          <div
            style={{
              display: 'flex',
              gap: '12px',
              marginTop: '8px',
            }}
          >
            {[
              { name: 'Sector 1', color: '#22c55e' },
              { name: 'Sector 2', color: '#eab308' },
              { name: 'Sector 3', color: '#9333ea' },
            ].map((sector) => (
              <div
                key={sector.name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <div
                  style={{
                    width: '12px',
                    height: '3px',
                    background: sector.color,
                    borderRadius: '2px',
                  }}
                />
                <span
                  style={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '11px',
                    fontWeight: 500,
                  }}
                >
                  {sector.name}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SVG Canvas */}
      <div
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <svg
          ref={svgRef}
          width={width}
          height={height}
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
          }}
        />
      </div>

      {/* Driver List */}
      <div
        style={{
          marginTop: '12px',
          maxHeight: '150px',
          overflowY: 'auto',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
            gap: '8px',
          }}
        >
          {drivers
            .sort((a, b) => a.position - b.position)
            .map((driver) => (
              <div
                key={driver.driverId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 8px',
                  background:
                    highlightedDriverId === driver.driverId
                      ? 'rgba(255, 255, 255, 0.15)'
                      : 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                }}
              >
                <div
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: driver.teamColor,
                  }}
                />
                <span
                  style={{
                    color: 'white',
                    fontSize: '11px',
                    fontWeight: 600,
                  }}
                >
                  P{driver.position}
                </span>
                <span
                  style={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '11px',
                  }}
                >
                  {driver.driverNumber}
                </span>
                <span
                  style={{
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontSize: '11px',
                    fontWeight: 500,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {driver.driverName.split(' ').pop()}
                </span>
              </div>
            ))}
        </div>
      </div>

      <style>{`
        .track-map-generator::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }

        .track-map-generator::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }

        .track-map-generator::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }

        .track-map-generator::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
};

export default TrackMapGenerator;
