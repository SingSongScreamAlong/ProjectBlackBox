import React from 'react';
import './TrainingDashboard.css';

interface Goal {
  id: string;
  title: string;
  description: string;
  category: 'speed' | 'consistency' | 'technique' | 'racecraft';
  priority: 'high' | 'medium' | 'low';
  progress: number;
  target: number;
  deadline: string;
  xpReward: number;
}

interface Skill {
  name: string;
  level: number;
  trend: 'up' | 'down' | 'stable';
  change: string;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  tier: 'gold' | 'silver' | 'bronze';
  unlocked: boolean;
}

const TrainingDashboard: React.FC = () => {
  // Sample data
  const goals: Goal[] = [
    {
      id: '1',
      title: 'Lap Time Mastery',
      description: 'Achieve a sub-1:28 lap time at Silverstone',
      category: 'speed',
      priority: 'high',
      progress: 72,
      target: 100,
      deadline: '3 days',
      xpReward: 500,
    },
    {
      id: '2',
      title: 'Consistency King',
      description: 'Complete 10 laps within 0.5s of each other',
      category: 'consistency',
      priority: 'medium',
      progress: 45,
      target: 100,
      deadline: '1 week',
      xpReward: 350,
    },
    {
      id: '3',
      title: 'Trail Braking Pro',
      description: 'Master trail braking through Copse corner',
      category: 'technique',
      priority: 'high',
      progress: 88,
      target: 100,
      deadline: '2 days',
      xpReward: 400,
    },
    {
      id: '4',
      title: 'Clean Racer',
      description: 'Complete 5 races with zero incidents',
      category: 'racecraft',
      priority: 'low',
      progress: 60,
      target: 100,
      deadline: '2 weeks',
      xpReward: 600,
    },
  ];

  const skills: Skill[] = [
    { name: 'Braking', level: 78, trend: 'up', change: '+3%' },
    { name: 'Corner Entry', level: 82, trend: 'up', change: '+5%' },
    { name: 'Throttle Control', level: 85, trend: 'stable', change: '0%' },
    { name: 'Tire Management', level: 65, trend: 'up', change: '+8%' },
    { name: 'Fuel Efficiency', level: 71, trend: 'down', change: '-2%' },
    { name: 'Racecraft', level: 74, trend: 'up', change: '+4%' },
  ];

  const achievements: Achievement[] = [
    { id: '1', name: 'Speed Demon', description: 'Top speed over 320 km/h', icon: '🚀', tier: 'gold', unlocked: true },
    { id: '2', name: 'Perfect Lap', description: 'All green sectors in one lap', icon: '💚', tier: 'gold', unlocked: true },
    { id: '3', name: 'Endurance', description: 'Complete a 60-minute session', icon: '⏱️', tier: 'silver', unlocked: true },
    { id: '4', name: 'Podium Finish', description: 'Finish in top 3', icon: '🏆', tier: 'bronze', unlocked: false },
  ];

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
            <div className="header-stat-value">Level 12</div>
            <div className="header-stat-label">Driver Level</div>
          </div>
          <div className="header-stat">
            <div className="header-stat-value">2,450</div>
            <div className="header-stat-label">Total XP</div>
          </div>
          <div className="header-stat">
            <div className="header-stat-value">4</div>
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
                      <span>{goal.deadline} left</span>
                    </div>
                    <div className="goal-xp">+{goal.xpReward} XP</div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Skills */}
          <section>
            <div className="section-header">
              <h2>Skill Ratings</h2>
              <span className="view-all">Details →</span>
            </div>
            <div className="skills-grid">
              {skills.map((skill) => (
                <div key={skill.name} className="skill-card">
                  <div className="skill-header">
                    <span className="skill-name">{skill.name}</span>
                    <span className="skill-level">{skill.level}</span>
                  </div>
                  <div className="skill-bar">
                    <div className="skill-fill" style={{ width: `${skill.level}%` }}></div>
                  </div>
                  <div className={`skill-trend ${skill.trend}`}>
                    {skill.trend === 'up' ? '↑' : skill.trend === 'down' ? '↓' : '→'}
                    <span>{skill.change} this week</span>
                  </div>
                </div>
              ))}
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
              <div className="profile-level">Level 12 • Pro Driver</div>
              <div className="xp-bar">
                <div className="xp-fill" style={{ width: '65%' }}></div>
              </div>
              <div className="xp-text">2,450 / 3,000 XP to Level 13</div>
            </div>
          </div>

          {/* Weekly Summary */}
          <div className="sidebar-section">
            <h3>This Week</h3>
            <div className="weekly-stats">
              <div className="weekly-stat">
                <div className="weekly-stat-value">12</div>
                <div className="weekly-stat-label">Sessions</div>
              </div>
              <div className="weekly-stat">
                <div className="weekly-stat-value">4.2h</div>
                <div className="weekly-stat-label">Track Time</div>
              </div>
              <div className="weekly-stat">
                <div className="weekly-stat-value">156</div>
                <div className="weekly-stat-label">Laps</div>
              </div>
              <div className="weekly-stat">
                <div className="weekly-stat-value">-0.8s</div>
                <div className="weekly-stat-label">Improvement</div>
              </div>
            </div>
          </div>

          {/* Achievements */}
          <div className="sidebar-section">
            <h3>Recent Achievements</h3>
            <div className="achievements-list">
              {achievements.map((achievement) => (
                <div 
                  key={achievement.id} 
                  className={`achievement-item ${!achievement.unlocked ? 'locked' : ''}`}
                >
                  <div className={`achievement-icon ${achievement.tier}`}>
                    {achievement.icon}
                  </div>
                  <div className="achievement-info">
                    <div className="achievement-name">{achievement.name}</div>
                    <div className="achievement-desc">{achievement.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrainingDashboard;
