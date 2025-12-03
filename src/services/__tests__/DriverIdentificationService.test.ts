/**
 * Unit tests for DriverIdentificationService
 */

import { DriverProfile } from '../DriverIdentificationService';

describe('DriverIdentificationService', () => {
  describe('DriverProfile Interface', () => {
    it('should have valid driver profile structure', () => {
      const mockProfile: DriverProfile = {
        id: 'test-id',
        name: 'Test Driver',
        email: 'test@example.com',
        team: 'Test Team',
        createdAt: Date.now(),
        updatedAt: Date.now(),
        identifiers: {
          username: 'testuser',
          iRacingId: '12345'
        }
      };

      expect(mockProfile.id).toBeDefined();
      expect(mockProfile.name).toBe('Test Driver');
      expect(mockProfile.email).toBe('test@example.com');
      expect(mockProfile.identifiers).toBeDefined();
    });

    it('should support optional fields', () => {
      const minimalProfile: DriverProfile = {
        id: 'minimal-id',
        name: 'Minimal Driver',
        createdAt: Date.now(),
        updatedAt: Date.now(),
        identifiers: {}
      };

      expect(minimalProfile.id).toBeDefined();
      expect(minimalProfile.name).toBe('Minimal Driver');
      expect(minimalProfile.email).toBeUndefined();
      expect(minimalProfile.team).toBeUndefined();
    });

    it('should support driving style metrics', () => {
      const profileWithStyle: DriverProfile = {
        id: 'style-id',
        name: 'Styled Driver',
        createdAt: Date.now(),
        updatedAt: Date.now(),
        identifiers: {},
        drivingStyle: {
          aggression: 75,
          consistency: 85,
          smoothness: 80,
          adaptability: 70,
          fuelEfficiency: 65,
          tireManagement: 90
        }
      };

      expect(profileWithStyle.drivingStyle).toBeDefined();
      expect(profileWithStyle.drivingStyle?.aggression).toBe(75);
      expect(profileWithStyle.drivingStyle?.consistency).toBe(85);
    });
  });
});
