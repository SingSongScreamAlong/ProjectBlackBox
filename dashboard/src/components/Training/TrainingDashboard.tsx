
import React, { useEffect, useState } from 'react';
import GoalCard from './GoalCard';
import { BACKEND_URL } from '../../config/environment';

const TrainingDashboard: React.FC = () => {
    const [goals, setGoals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchGoals();
    }, []);

    const fetchGoals = async () => {
        try {
            // Assuming auth token is stored in localStorage or handled by fetch wrapper
            // For now, using basic fetch
            const token = localStorage.getItem('token');
            const res = await fetch(`${BACKEND_URL}/api/training/goals`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.ok) {
                const data = await res.json();
                setGoals(data.goals);
            }
        } catch (error) {
            console.error('Failed to fetch goals', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 bg-gray-900 min-h-screen text-white">
            <header className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Driver Training</h1>
                <p className="text-gray-400">Track your progress and achieve your goals.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Active Goals Column */}
                <div className="lg:col-span-2">
                    <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Active Goals</h2>

                    {loading ? (
                        <p>Loading goals...</p>
                    ) : goals.length === 0 ? (
                        <div className="bg-gray-800 p-8 rounded-lg text-center">
                            <p className="text-gray-400 mb-4">No active training goals.</p>
                            <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded">
                                Create Goal
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {goals.map(goal => (
                                <GoalCard key={goal.id} goal={goal} />
                            ))}
                        </div>
                    )}
                </div>

                {/* Sidebar / Stats */}
                <div>
                    <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Skill Overview</h2>
                    <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-gray-400 text-sm">Skill radar chart coming soon...</p>
                    </div>

                    <h2 className="text-xl font-semibold mt-8 mb-4 border-b border-gray-700 pb-2">Recent Badges</h2>
                    <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-gray-400 text-sm">No badges earned yet.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TrainingDashboard;
