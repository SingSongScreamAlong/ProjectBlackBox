import React from 'react';
import { CoachingInsight, DriverSkillAnalysis } from '../../services/WebSocketService';

interface AICoachingProps {
  insights: CoachingInsight[] | null;
  skillAnalysis: DriverSkillAnalysis | null;
}

const AICoaching: React.FC<AICoachingProps> = ({ insights, skillAnalysis }) => {
  // Use provided data
  const displayInsights = insights || [];
  const displaySkillAnalysis = skillAnalysis || { strengths: [], focusAreas: [], overallRating: 0 };


  return (
    <div className="panel ai-panel">
      <div className="panel-header">COACH - ACTIONABLE INSIGHTS</div>
      <div className="panel-content">
        <div className="ai-suggestions">
          {displayInsights.length > 0 ? (
            displayInsights.map((insight, index) => (
              <div key={`insight-${index}`} className={`ai-suggestion ${insight.priority}`}>
                <div className="suggestion-header">
                  <div className="suggestion-priority">
                    {insight.category || insight.priority}
                  </div>
                  <div className="suggestion-confidence">{insight.confidence}% confidence</div>
                </div>
                <div className="suggestion-title">{insight.title}</div>
                <div className="suggestion-description">{insight.description}</div>
                <div className="suggestion-impact">{insight.impact}</div>
              </div>
            ))
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#888', fontStyle: 'italic' }}>
              No insights available
            </div>
          )}

          {/* Driver Skill Analysis */}
          <div style={{ marginTop: '16px' }}>
            <div className="section-title">DRIVER SKILL ANALYSIS</div>
            <div className="ai-suggestions">
              <div className="ai-suggestion">
                <div className="suggestion-header">
                  <div className="suggestion-priority">Strengths</div>
                  <div className="suggestion-confidence">Overall: {displaySkillAnalysis.overallRating}%</div>
                </div>
                <div className="suggestion-description" style={{ marginBottom: '8px' }}>
                  {displaySkillAnalysis.strengths.map((strength, index) => (
                    <React.Fragment key={`strength-${index}`}>
                      • {strength.skill}: {strength.rating}% ({getRatingText(strength.rating)})<br />
                    </React.Fragment>
                  ))}
                </div>
              </div>

              <div className="ai-suggestion warning">
                <div className="suggestion-header">
                  <div className="suggestion-priority">Focus Areas</div>
                  <div className="suggestion-confidence">
                    Improvement: {calculateImprovementPotential(displaySkillAnalysis.focusAreas)}%
                  </div>
                </div>
                <div className="suggestion-description" style={{ marginBottom: '8px' }}>
                  {displaySkillAnalysis.focusAreas.map((area, index) => (
                    <React.Fragment key={`area-${index}`}>
                      • {area.skill}: {area.rating}% ({getRatingText(area.rating)})<br />
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to get text rating based on numerical score
const getRatingText = (rating: number): string => {
  if (rating >= 90) return 'Excellent';
  if (rating >= 80) return 'Good';
  if (rating >= 70) return 'Fair';
  if (rating >= 60) return 'Needs Work';
  return 'Poor';
};

// Helper function to calculate improvement potential
const calculateImprovementPotential = (focusAreas: Array<{ skill: string; rating: number }>): number => {
  if (focusAreas.length === 0) return 0;

  // Calculate how much room for improvement exists (100 - average rating)
  const avgRating = focusAreas.reduce((sum, area) => sum + area.rating, 0) / focusAreas.length;
  return Math.round((100 - avgRating) / 3); // Divide by 3 to get a reasonable percentage
};

export default AICoaching;
