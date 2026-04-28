import { useEffect, useState } from 'react';
import { Users, Clock3, CheckCircle, XCircle, LogOut, Zap, Target } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminDashboard({ onNavigate, onLogout }) {
  const STORAGE_KEY = 'engageXUser';
  const [pendingTasks, setPendingTasks] = useState([]);
  const [approvedTasks, setApprovedTasks] = useState([]);
  const [platformDistribution, setPlatformDistribution] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({
    totalBuyerAccounts: 0,
    totalSellerAccounts: 0,
    totalTasks: 0,
    pendingTasks: 0,
    approvedTasks: 0,
    rejectedTasks: 0,
    completedTasks: 0,
  });

  const fetchDashboardData = async () => {
    try {
      const [pendingResponse, statsResponse] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/admin-pending-tasks/'),
        fetch('http://127.0.0.1:8000/api/admin-dashboard-stats/'),
      ]);

      const pendingData = await pendingResponse.json();
      const statsData = await statsResponse.json();

      if (pendingResponse.ok) {
        setPendingTasks(pendingData.tasks || []);
      }

      if (statsResponse.ok) {
        setDashboardStats(statsData.stats || {});
        setApprovedTasks(statsData.approvedTasksList || []);
        setPlatformDistribution(statsData.platformDistribution || []);
      }
    } catch (error) {
      console.error('Admin dashboard fetch error:', error);
    }
  };

  const fetchSellers = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/seller-list/');
      const data = await response.json();

      if (response.ok) {
        return data.sellers || [];
      }
    } catch (error) {
      console.error('Seller list fetch error:', error);
    }

    return [];
  };

  const fetchJobs = async (sellersObj) => {
    try {
      const totalJobs = 20;
      const response = await fetch('http://127.0.0.1:8000/ml/allocate-jobs/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ total_jobs: totalJobs, sellers: sellersObj }),
      });
      const data = await response.json();

      if (response.ok) {
        return data.job_allocation;
      }
    } catch (error) {
      console.error('Job assignment error:', error);
    }

    return null;
  };

  const handleApprove = async (taskId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/approve-task/${taskId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();

      if (response.ok) {
        const sellersObj = await fetchSellers();
        const allocation = await fetchJobs(sellersObj);

        if (allocation && sellersObj.length > 0) {
          const formattedJobs = {
            rate1: allocation['1'] || 0,
            rate2: allocation['2'] || 0,
            rate3: allocation['3'] || 0,
            rate4: allocation['4'] || 0,
            rate5: allocation['5'] || 0,
          };

          await fetch('http://127.0.0.1:8000/api/assign-jobs/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              sellers: sellersObj,
              jobs: formattedJobs,
              taskId,
            }),
          });
        }

        alert(data.message);
        fetchDashboardData();
      } else {
        alert(data.error || 'Approve failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  const handleReject = async (taskId) => {
    const reason = prompt('Enter rejection reason') || '';

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/reject-task/${taskId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        fetchDashboardData();
      } else {
        alert(data.error || 'Reject failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleLogoutClick = () => {
    localStorage.removeItem(STORAGE_KEY);

    if (onLogout) {
      onLogout();
      return;
    }

    window.location.href = '/';
  };

  const stats = [
    {
      label: 'Buyer Accounts',
      value: dashboardStats.totalBuyerAccounts,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      label: 'Total Tasks',
      value: dashboardStats.totalTasks,
      icon: Target,
      color: 'text-purple-600',
      bg: 'bg-purple-100',
    },
    {
      label: 'Pending Tasks',
      value: dashboardStats.pendingTasks,
      icon: Clock3,
      color: 'text-orange-600',
      bg: 'bg-orange-100',
    },
    {
      label: 'Approved Tasks',
      value: dashboardStats.approvedTasks,
      icon: CheckCircle,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                <Zap className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <span className="text-gray-900 text-sm sm:text-base">Engage X</span>
              <Badge className="ml-1 sm:ml-2 bg-purple-100 text-purple-700 hover:bg-purple-100 text-xs sm:text-sm">Admin</Badge>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <Button variant="ghost" size="sm" onClick={handleLogoutClick} className="text-xs sm:text-sm">
                <LogOut className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600 text-sm sm:text-base">Only real buyer portal task records are shown here.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="border-gray-200 rounded-2xl hover:shadow-lg transition-shadow">
              <CardContent className="pt-4 sm:pt-6 p-4 sm:p-6">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-xs sm:text-sm text-gray-600 mb-1">{stat.label}</p>
                    <p className="text-gray-900 text-lg sm:text-2xl">{stat.value}</p>
                  </div>
                  <div className={`w-10 h-10 sm:w-12 sm:h-12 ${stat.bg} rounded-xl flex items-center justify-center`}>
                    <stat.icon className={`w-5 h-5 sm:w-6 sm:h-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-8 mb-6 sm:mb-8">
          <Card className="border-gray-200 rounded-2xl">
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-gray-900 text-base sm:text-lg">Task Status Summary</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Real admin approval totals</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 p-4 sm:p-6 pt-0">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Pending</span>
                <span className="text-orange-600">{dashboardStats.pendingTasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Approved</span>
                <span className="text-green-600">{dashboardStats.approvedTasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Rejected</span>
                <span className="text-red-600">{dashboardStats.rejectedTasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Completed</span>
                <span className="text-blue-600">{dashboardStats.completedTasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Seller Accounts</span>
                <span className="text-gray-900">{dashboardStats.totalSellerAccounts}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-gray-200 rounded-2xl">
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-gray-900 text-base sm:text-lg">Platform Distribution</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Tasks posted by buyers</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={platformDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                  <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <Card className="border-gray-200 rounded-2xl">
          <CardHeader className="p-4 sm:p-6">
            <Tabs defaultValue="pending" className="w-full">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <CardTitle className="text-gray-900 text-base sm:text-lg">Buyer Task Records</CardTitle>
                  <CardDescription className="text-xs sm:text-sm">Pending and approved tasks posted from buyer portal</CardDescription>
                </div>
                <TabsList className="w-full sm:w-auto">
                  <TabsTrigger value="pending" className="flex-1 sm:flex-none">Pending</TabsTrigger>
                  <TabsTrigger value="approved" className="flex-1 sm:flex-none">Approved</TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="pending" className="space-y-3 sm:space-y-4 mt-6">
                {pendingTasks.length === 0 && (
                  <div className="text-center py-8 text-gray-500 text-sm">No pending buyer tasks</div>
                )}

                {pendingTasks.map((task) => (
                  <div key={task.id} className="border border-gray-200 rounded-xl p-3 sm:p-4 hover:border-orange-200 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-3 gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <h3 className="text-gray-900 text-sm sm:text-base">{task.title}</h3>
                          <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">Pending</Badge>
                        </div>
                        <p className="text-xs sm:text-sm text-gray-600">Buyer: {task.buyerName}</p>
                        <p className="text-xs sm:text-sm text-gray-500 mt-1">{task.taskType} - Goal: {task.goal}</p>
                      </div>
                      <span className="text-xs sm:text-sm text-gray-500 whitespace-nowrap">{task.created}</span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                        <span className="text-xs sm:text-sm text-gray-600">Platform:</span>
                        <Badge variant="outline" className="text-xs">{task.platform}</Badge>
                        <span className="text-xs sm:text-sm text-gray-600">Price:</span>
                        <span className="text-gray-900 text-xs sm:text-sm">${task.pricePerAction}</span>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white rounded-full text-xs h-8" onClick={() => handleApprove(task.id)}>
                          <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                          <span className="hidden sm:inline">Approve</span>
                        </Button>
                        <Button size="sm" variant="destructive" className="rounded-full text-xs h-8" onClick={() => handleReject(task.id)}>
                          <XCircle className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                          <span className="hidden sm:inline">Reject</span>
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </TabsContent>

              <TabsContent value="approved" className="space-y-3 sm:space-y-4 mt-6">
                {approvedTasks.length === 0 && (
                  <div className="text-center py-8 text-gray-500 text-sm">No approved buyer tasks yet</div>
                )}

                {approvedTasks.map((task) => (
                  <div key={task.id} className="border border-gray-200 rounded-xl p-3 sm:p-4 hover:border-green-200 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-3 gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <h3 className="text-gray-900 text-sm sm:text-base">{task.title}</h3>
                          <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Approved</Badge>
                        </div>
                        <p className="text-xs sm:text-sm text-gray-600">Buyer: {task.buyerName}</p>
                        <p className="text-xs sm:text-sm text-gray-500 mt-1">
                          {task.taskType} - Goal: {task.goal} - Progress: {task.progressed}
                        </p>
                      </div>
                      <span className="text-xs sm:text-sm text-gray-500 whitespace-nowrap">{task.created}</span>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                        <span className="text-xs sm:text-sm text-gray-600">Platform:</span>
                        <Badge variant="outline" className="text-xs">{task.platform}</Badge>
                        <span className="text-xs sm:text-sm text-gray-600">Price:</span>
                        <span className="text-gray-900 text-xs sm:text-sm">${task.pricePerAction}</span>
                      </div>
                      <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">{task.status}</Badge>
                    </div>
                  </div>
                ))}
              </TabsContent>
            </Tabs>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
