import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../redux/store';
import { DriverComparison as DriverComparisonType } from '../../redux/driversSlice';
import multiDriverService from '../../services/MultiDriverService';

/**
 * DriverComparison component for comparing telemetry data between two drivers
 */
const DriverComparison: React.FC = () => {
  const [driver1Id, setDriver1Id] = useState<string>('');
  const [driver2Id, setDriver2Id] = useState<string>('');
  const [comparisonId, setComparisonId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const { drivers, driverComparisons } = useSelector((state: RootState) => state.drivers);
  
  // Get the current comparison data if available
  const currentComparison = comparisonId 
    ? driverComparisons.find((c: DriverComparisonType) => c.driverId1 === driver1Id && c.driverId2 === driver2Id) 
    : null;

  // Request comparison data when both drivers are selected
  const handleCompare = () => {
    if (driver1Id && driver2Id && driver1Id !== driver2Id) {
      setIsLoading(true);
      const id = multiDriverService.requestDriverComparison(driver1Id, driver2Id);
      setComparisonId(id);
    }
  };

  // Reset loading state when comparison data is received
  useEffect(() => {
    if (currentComparison && isLoading) {
      setIsLoading(false);
    }
  }, [currentComparison, isLoading]);

  // Format time values (mm:ss.SSS)
  const formatTime = (timeInSeconds: number): string => {
    if (!timeInSeconds) return '00:00.000';
    
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
    
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
  };

  // Calculate percentage difference for comparison bars
  const calculatePercentage = (value1: number, value2: number): { driver1: number, driver2: number } => {
    if (!value1 && !value2) return { driver1: 50, driver2: 50 };
    
    const total = Math.abs(value1) + Math.abs(value2);
    const driver1Percent = (Math.abs(value1) / total) * 100;
    const driver2Percent = (Math.abs(value2) / total) * 100;
    
    return { driver1: driver1Percent, driver2: driver2Percent };
  };

  // Get driver name by ID
  const getDriverName = (id: string): string => {
    const driver = drivers.find(d => d.id === id);
    return driver ? driver.name : 'Unknown Driver';
  };

  return (
    <div className="driver-comparison">
      <div className="comparison-selector">
        <select 
          className="comparison-driver-select"
          value={driver1Id}
          onChange={(e) => setDriver1Id(e.target.value)}
        >
          <option value="">Select Driver 1</option>
          {drivers.map(driver => (
            <option key={driver.id} value={driver.id}>
              {driver.name}
            </option>
          ))}
        </select>
        
        <select 
          className="comparison-driver-select"
          value={driver2Id}
          onChange={(e) => setDriver2Id(e.target.value)}
        >
          <option value="">Select Driver 2</option>
          {drivers.map(driver => (
            <option key={driver.id} value={driver.id}>
              {driver.name}
            </option>
          ))}
        </select>
        
        <button 
          className="compare-button"
          onClick={handleCompare}
          disabled={!driver1Id || !driver2Id || driver1Id === driver2Id || isLoading}
        >
          {isLoading ? 'Loading...' : 'Compare'}
        </button>
      </div>
      
      {currentComparison ? (
        <div className="comparison-results">
          {/* Lap Time Comparison */}
          <div className="comparison-metric">
            <div className="metric-header">Lap Time</div>
            <div className="metric-values">
              <div className="driver-value">
                {formatTime(currentComparison.metrics.lapTime.driver1)}
              </div>
              <div className="driver-value">
                {formatTime(currentComparison.metrics.lapTime.driver2)}
              </div>
            </div>
            <div className="comparison-bar">
              {currentComparison.metrics.lapTime.driver1 && currentComparison.metrics.lapTime.driver2 && (
                <>
                  <div 
                    className="driver1-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.lapTime.driver1, 
                        currentComparison.metrics.lapTime.driver2
                      ).driver1}%` 
                    }}
                  />
                  <div 
                    className="driver2-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.lapTime.driver1, 
                        currentComparison.metrics.lapTime.driver2
                      ).driver2}%` 
                    }}
                  />
                </>
              )}
            </div>
          </div>
          
          {/* Sector Times Comparison */}
          <div className="comparison-metric">
            <div className="metric-header">Sector 1</div>
            <div className="metric-values">
              <div className="driver-value">
                {formatTime(currentComparison.metrics.sectors.sector1.driver1)}
              </div>
              <div className="driver-value">
                {formatTime(currentComparison.metrics.sectors.sector1.driver2)}
              </div>
            </div>
            <div className="comparison-bar">
              {currentComparison.metrics.sectors.sector1.driver1 && currentComparison.metrics.sectors.sector1.driver2 && (
                <>
                  <div 
                    className="driver1-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.sectors.sector1.driver1, 
                        currentComparison.metrics.sectors.sector1.driver2
                      ).driver1}%` 
                    }}
                  />
                  <div 
                    className="driver2-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.sectors.sector1.driver1, 
                        currentComparison.metrics.sectors.sector1.driver2
                      ).driver2}%` 
                    }}
                  />
                </>
              )}
            </div>
          </div>
          
          <div className="comparison-metric">
            <div className="metric-header">Sector 2</div>
            <div className="metric-values">
              <div className="driver-value">
                {formatTime(currentComparison.metrics.sectors.sector2.driver1)}
              </div>
              <div className="driver-value">
                {formatTime(currentComparison.metrics.sectors.sector2.driver2)}
              </div>
            </div>
            <div className="comparison-bar">
              {currentComparison.metrics.sectors.sector2.driver1 && currentComparison.metrics.sectors.sector2.driver2 && (
                <>
                  <div 
                    className="driver1-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.sectors.sector2.driver1, 
                        currentComparison.metrics.sectors.sector2.driver2
                      ).driver1}%` 
                    }}
                  />
                  <div 
                    className="driver2-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.sectors.sector2.driver1, 
                        currentComparison.metrics.sectors.sector2.driver2
                      ).driver2}%` 
                    }}
                  />
                </>
              )}
            </div>
          </div>
          
          <div className="comparison-metric">
            <div className="metric-header">Sector 3</div>
            <div className="metric-values">
              <div className="driver-value">
                {formatTime(currentComparison.metrics.sectors.sector3.driver1)}
              </div>
              <div className="driver-value">
                {formatTime(currentComparison.metrics.sectors.sector3.driver2)}
              </div>
            </div>
            <div className="comparison-bar">
              {currentComparison.metrics.sectors.sector3.driver1 && currentComparison.metrics.sectors.sector3.driver2 && (
                <>
                  <div 
                    className="driver1-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.sectors.sector3.driver1, 
                        currentComparison.metrics.sectors.sector3.driver2
                      ).driver1}%` 
                    }}
                  />
                  <div 
                    className="driver2-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.sectors.sector3.driver1, 
                        currentComparison.metrics.sectors.sector3.driver2
                      ).driver2}%` 
                    }}
                  />
                </>
              )}
            </div>
          </div>
          
          {/* Fuel Usage Comparison */}
          <div className="comparison-metric">
            <div className="metric-header">Fuel Usage (L/lap)</div>
            <div className="metric-values">
              <div className="driver-value">
                {currentComparison.metrics.fuelUsage.driver1.toFixed(2)}
              </div>
              <div className="driver-value">
                {currentComparison.metrics.fuelUsage.driver2.toFixed(2)}
              </div>
            </div>
            <div className="comparison-bar">
              {currentComparison.metrics.fuelUsage.driver1 && currentComparison.metrics.fuelUsage.driver2 && (
                <>
                  <div 
                    className="driver1-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.fuelUsage.driver1, 
                        currentComparison.metrics.fuelUsage.driver2
                      ).driver1}%` 
                    }}
                  />
                  <div 
                    className="driver2-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        currentComparison.metrics.fuelUsage.driver1, 
                        currentComparison.metrics.fuelUsage.driver2
                      ).driver2}%` 
                    }}
                  />
                </>
              )}
            </div>
          </div>
          
          {/* Tire Wear Comparison */}
          <div className="comparison-metric">
            <div className="metric-header">Average Tire Wear (%)</div>
            <div className="metric-values">
              <div className="driver-value">
                {(
                  (currentComparison.metrics.tireWear.driver1.fl +
                   currentComparison.metrics.tireWear.driver1.fr +
                   currentComparison.metrics.tireWear.driver1.rl +
                   currentComparison.metrics.tireWear.driver1.rr) / 4
                ).toFixed(1)}%
              </div>
              <div className="driver-value">
                {(
                  (currentComparison.metrics.tireWear.driver2.fl +
                   currentComparison.metrics.tireWear.driver2.fr +
                   currentComparison.metrics.tireWear.driver2.rl +
                   currentComparison.metrics.tireWear.driver2.rr) / 4
                ).toFixed(1)}%
              </div>
            </div>
            <div className="comparison-bar">
              {currentComparison.metrics.tireWear.driver1.fl && currentComparison.metrics.tireWear.driver2.fl && (
                <>
                  <div 
                    className="driver1-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        (currentComparison.metrics.tireWear.driver1.fl +
                         currentComparison.metrics.tireWear.driver1.fr +
                         currentComparison.metrics.tireWear.driver1.rl +
                         currentComparison.metrics.tireWear.driver1.rr) / 4,
                        (currentComparison.metrics.tireWear.driver2.fl +
                         currentComparison.metrics.tireWear.driver2.fr +
                         currentComparison.metrics.tireWear.driver2.rl +
                         currentComparison.metrics.tireWear.driver2.rr) / 4
                      ).driver1}%` 
                    }}
                  />
                  <div 
                    className="driver2-bar" 
                    style={{ 
                      width: `${calculatePercentage(
                        (currentComparison.metrics.tireWear.driver1.fl +
                         currentComparison.metrics.tireWear.driver1.fr +
                         currentComparison.metrics.tireWear.driver1.rl +
                         currentComparison.metrics.tireWear.driver1.rr) / 4,
                        (currentComparison.metrics.tireWear.driver2.fl +
                         currentComparison.metrics.tireWear.driver2.fr +
                         currentComparison.metrics.tireWear.driver2.rl +
                         currentComparison.metrics.tireWear.driver2.rr) / 4
                      ).driver2}%` 
                    }}
                  />
                </>
              )}
            </div>
          </div>
          
          <div className="comparison-legend">
            <div className="legend-item">
              <div className="legend-color driver1-color"></div>
              <div className="legend-label">{getDriverName(driver1Id)}</div>
            </div>
            <div className="legend-item">
              <div className="legend-color driver2-color"></div>
              <div className="legend-label">{getDriverName(driver2Id)}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="no-comparison-message">
          {driver1Id && driver2Id 
            ? 'Click Compare to view driver comparison data'
            : 'Select two drivers to compare their telemetry data'}
        </div>
      )}
    </div>
  );
};

export default DriverComparison;
