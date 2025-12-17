import React, { useState, useEffect } from 'react';
import TrainingService, { TrainingGoal, Badge } from '../../services/TrainingService';
import './TrainingDashboard.css';

// Stats & Skills - waiting for API implementation
// Removed mock data as requested.

const TrainingDashboard: React.FC = () => {
  const [goals, setGoals] = useState<TrainingGoal[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);

  // Initialize with overrides or defaults - eventually fetch from API
  const currentLevel = 1;
  const totalXp = 0;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [fetchedGoals, fetchedBadges] = await Promise.all([
          TrainingService.getGoals(),
          TrainingService.getBadges()
        ]);
        setGoals(fetchedGoals);
        setBadges(fetchedBadges);
      } catch (error) {
        console.error("Failed to load training data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'speed': return '⚡';
      case 'consistency': return '🎯';
      case 'technique': return '🔧';
      case 'racecraft': return '🏎️';
      default: return '📊';
    }
  };

  return (
    <div className="training-page">
      <div className="training-header">
        <h1>🎓 Driver Training</h1>
        <div className="header-stats">
          <div className="header-stat">
            <div className="header-stat-value">Level {currentLevel}</div>
            <div className="header-stat-label">Driver Level</div>
          </div>
          <div className="header-stat">
            <div className="header-stat-value">{totalXp.toLocaleString()}</div>
            <div className="header-stat-label">Total XP</div>
          </div>
          <div className="header-stat">
            <div className="header-stat-value">{goals.length}</div>
            <div className="header-stat-label">Active Goals</div>
          </div>
        </div>
      </div>

      <div className="training-content">
        {/* Main Content */}
        <div className="training-main">
          {/* Active Goals */}
          <section>
            <div className="section-header">
              <h2>Active Goals</h2>
              <span className="view-all">View All →</span>
            </div>
            {goals.length > 0 ? (
              <div className="goals-grid">
                {goals.map((goal) => (
                  <div key={goal.id} className="goal-card">
                    <div className="goal-header">
                      <div className={`goal-icon ${goal.category}`}>
                        {getCategoryIcon(goal.category)}
                      </div>
                      <span className={`goal-priority ${goal.priority}`}>{goal.priority}</span>
                    </div>
                    <div className="goal-title">{goal.title}</div>
                    <div className="goal-description">{goal.description}</div>
                    <div className="goal-progress">
                      <div className="progress-header">
                        <span className="progress-label">Progress</span>
                        <span className="progress-value">{goal.progress}%</span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className={`progress-fill ${goal.category}`}
                          style={{ width: `${goal.progress}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="goal-footer">
                      <div className="goal-deadline">
                        <span>⏰</span>
                        <span>{goal.deadline || 'Ongoing'} left</span>
                      </div>
                      <div className="goal-xp">+{goal.xpReward} XP</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-data-message" style={{ padding: '2rem', textAlign: 'center', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '12px' }}>
                No active goals. Training plan complete!
              </div>
            )}
          </section>

          {/* Skills */}
          <section>
            <div className="section-header">
              <h2>Skill Ratings</h2>
              <span className="view-all">Details →</span>
            </div>
            {/* Removed mock skills. Requires implementation of SkillService */}
            <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '12px', color: '#888' }}>
              Skills data not available. Complete training sessions to generate ratings.
            </div>
          </section>
        </div>

        {/* Sidebar */}
        <div className="training-sidebar">
          {/* Driver Profile */}
          <div className="sidebar-section">
            <div className="driver-profile">
              <div className="profile-avatar">🏎️</div>
              <div className="profile-name">Driver</div>
              <div className="profile-level">Level {currentLevel} • Rookie</div>
              <div className="xp-bar">
                <div className="xp-fill" style={{ width: '0%' }}></div>
              </div>
              <div className="xp-text">{totalXp} / 1,000 XP to Level {currentLevel + 1}</div>
            </div>
          </div>

          {/* Weekly Summary */}
          <div className="sidebar-section">
            <h3>This Week</h3>
            {/* Removed mock weekly stats */}
            <div style={{ padding: '1rem', color: '#666', fontSize: '0.9rem' }}>
              No activity recorded this week.
            </div>
          </div>

          {/* Achievements (Badges) */}
          <div className="sidebar-section">
            <h3>Recent Badges</h3>
            <div className="achievements-list">
              {badges.map((badge) => (
                <div
                  key={badge.id}
                  className={`achievement-item ${!badge.unlocked ? 'locked' : ''}`}
                >
                  <div className={`achievement-icon ${badge.tier}`}>
                    {badge.icon}
                  </div>
                  <div className="achievement-info">
                    <div className="achievement-name">{badge.name}</div>
                    <div className="achievement-desc">{badge.description}</div>
                  </div>
                </div>
              ))}
              {badges.length === 0 && <div style={{ color: '#666', fontSize: '12px' }}>No badges earned yet.</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrainingDashboard;
