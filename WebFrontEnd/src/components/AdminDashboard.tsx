import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Users, DollarSign, AlertTriangle, TrendingUp, CheckCircle, XCircle, Eye, Ban, LogOut, Zap } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE_URL = 'http://127.0.0.1:8000';

const emptyDashboardData = {
  stats: {
    totalUsers: 0,
    revenue: 0,
    activeTasks: 0,
    pendingTasks: 0,
  },
  revenueData: [],
  taskDistribution: [],
  recentUsers: [],
  flaggedUsers: [],
};

export default function AdminDashboard({ onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const adminUser = location.state?.userData;
  const [pendingTasks, setPendingTasks] = useState([]);
  const [activeTasks, setActiveTasks] = useState([]);
  const [taskView, setTaskView] = useState('pending');
  const [dashboardData, setDashboardData] = useState(emptyDashboardData);
  const [isLoading, setIsLoading] = useState(true);

  const stats = [
    { label: 'Total Users', value: dashboardData.stats.totalUsers, icon: Users, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Revenue', value: `$${dashboardData.stats.revenue.toFixed(2)}`, icon: DollarSign, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Active Tasks', value: dashboardData.stats.activeTasks, icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-100', view: 'active' },
    { label: 'Pending Tasks', value: dashboardData.stats.pendingTasks, icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-100', view: 'pending' },
  ];

  const fetchAdminSummary = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin-dashboard-summary/`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Admin summary fetch failed');
    }

    setDashboardData({
      stats: data.stats || emptyDashboardData.stats,
      revenueData: data.revenueData || [],
      taskDistribution: data.taskDistribution || [],
      recentUsers: data.recentUsers || [],
      flaggedUsers: data.flaggedUsers || [],
    });
  };

  const fetchPendingTasks = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin-pending-tasks/`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Pending tasks fetch failed');
    }

    setPendingTasks(data.tasks || []);
  };

  const fetchActiveTasks = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin-active-tasks/`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Active tasks fetch failed');
    }

    setActiveTasks(data.tasks || []);
  };

  const refreshAdminData = async ({ showLoader = true, showAlert = true } = {}) => {
    if (showLoader) {
      setIsLoading(true);
    }

    try {
      await Promise.all([fetchAdminSummary(), fetchPendingTasks(), fetchActiveTasks()]);
    } catch (error) {
      console.error('Admin dashboard refresh error:', error);
      if (showAlert) {
        alert('Could not load admin dashboard data');
      }
    } finally {
      if (showLoader) {
        setIsLoading(false);
      }
    }
  };

  const fetchSellers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/seller-list/`);
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
      const response = await fetch(`${API_BASE_URL}/ml/allocate-jobs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ total_jobs: 20, sellers: sellersObj }),
      });
      const data = await response.json();
      if (response.ok) {
        return data.job_allocation || {};
      }
    } catch (error) {
      console.error('Job assignment error:', error);
    }

    return {};
  };

  const assignJobsToSellers = async (taskId, sellersObj, allocation) => {
    const formattedJobs = {
      rate1: allocation['1'] || 0,
      rate2: allocation['2'] || 0,
      rate3: allocation['3'] || 0,
      rate4: allocation['4'] || 0,
      rate5: allocation['5'] || 0,
    };

    const response = await fetch(`${API_BASE_URL}/api/assign-jobs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sellers: sellersObj,
        jobs: formattedJobs,
        taskId,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Assign jobs failed');
    }
  };

  const handleApprove = async (taskId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/approve-task/${taskId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();

      if (!response.ok) {
        alert(data.error || 'Approve failed');
        return;
      }

      const sellersObj = await fetchSellers();
      const allocation = await fetchJobs(sellersObj);
      await assignJobsToSellers(taskId, sellersObj, allocation);
      alert(data.message);
      refreshAdminData();
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  const handleReject = async (taskId) => {
    const reason = prompt('Enter rejection reason') || '';

    try {
      const response = await fetch(`${API_BASE_URL}/api/reject-task/${taskId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        refreshAdminData();
      } else {
        alert(data.error || 'Reject failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
      return;
    }

    navigate('/');
  };

  useEffect(() => {
    refreshAdminData();
    const refreshInterval = window.setInterval(() => {
      refreshAdminData({ showLoader: false, showAlert: false });
    }, 10000);

    return () => window.clearInterval(refreshInterval);
  }, []);

  const getSeverityBadge = () => {
    return <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">Pending</Badge>;
  };

  const getUserTypeBadge = (type) => {
    if (type === 'Buyer') {
      return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">Buyer</Badge>;
    }
    if (type === 'Admin') {
      return <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-100">Admin</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Seller</Badge>;
  };

  const getStatusBadge = (status) => {
    if (status === 'Active') {
      return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Active</Badge>;
    }
    return <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-100">Suspended</Badge>;
  };

  const EmptyState = ({ message }) => (
    <div className="h-[250px] flex items-center justify-center text-sm text-gray-500">
      {message}
    </div>
  );

  const UserList = ({ users, emptyMessage, showReports = false }) => {
    if (!users.length) {
      return (
        <div className="text-center py-8 text-gray-500">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-xs sm:text-sm">{emptyMessage}</p>
        </div>
      );
    }

    return users.map((user) => (
      <div key={user.id} className="border border-gray-200 rounded-lg p-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0">
            <p className="text-xs sm:text-sm text-gray-900 truncate">{user.name}</p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {getUserTypeBadge(user.type)}
          {getStatusBadge(user.status)}
          {showReports && <Badge variant="outline" className="text-xs">{user.reports} reports</Badge>}
        </div>
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Joined {user.joined || 'N/A'}</span>
          <Button size="sm" variant="ghost" className="h-6 px-2">
            <Ban className="w-3 h-3" />
          </Button>
        </div>
      </div>
    ));
  };

  const visibleTasks = taskView === 'active' ? activeTasks : pendingTasks;

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
              {adminUser?.userName && <span className="hidden sm:inline text-sm text-gray-500">{adminUser.userName}</span>}
            </div>
            <Button variant="ghost" size="sm" onClick={handleLogout} className="text-xs sm:text-sm">
              <LogOut className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600 text-sm sm:text-base">Monitor platform activity and manage users and tasks.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
          {stats.map((stat) => (
            <Card
              key={stat.label}
              onClick={() => stat.view && setTaskView(stat.view)}
              className={`border-gray-200 rounded-2xl hover:shadow-lg transition-shadow ${stat.view ? 'cursor-pointer' : ''} ${taskView === stat.view ? 'ring-2 ring-green-500' : ''}`}
            >
              <CardContent className="pt-4 sm:pt-6 p-4 sm:p-6">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-xs sm:text-sm text-gray-600 mb-1">{stat.label}</p>
                    <p className="text-gray-900 text-lg sm:text-2xl">{isLoading ? '...' : stat.value}</p>
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
              <CardTitle className="text-gray-900 text-base sm:text-lg">Revenue Overview</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Monthly escrow revenue and user growth from the database</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              {dashboardData.revenueData.length ? (
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={dashboardData.revenueData}>
                    <defs>
                      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} />
                    <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px' }} />
                    <Area type="monotone" dataKey="revenue" stroke="#10b981" fillOpacity={1} fill="url(#colorRevenue)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No revenue data yet" />
              )}
            </CardContent>
          </Card>

          <Card className="border-gray-200 rounded-2xl">
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-gray-900 text-base sm:text-lg">Task Distribution</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Tasks by platform from buyer task records</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              {dashboardData.taskDistribution.length ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={dashboardData.taskDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} />
                    <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px' }} />
                    <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message="No tasks created yet" />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8">
          <div className="lg:col-span-2">
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader className="p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <CardTitle className="text-gray-900 text-base sm:text-lg">
                      {taskView === 'active' ? 'Active Tasks' : 'Pending Tasks'}
                    </CardTitle>
                    <CardDescription className="text-xs sm:text-sm">
                      {taskView === 'active'
                        ? 'Tasks that are live right now'
                        : 'Review buyer tasks before they go live on the portal'}
                    </CardDescription>
                  </div>
                  <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100 w-fit text-xs sm:text-sm">
                    {visibleTasks.length} {taskView === 'active' ? 'Active' : 'Pending'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-4 sm:p-6 pt-0">
                <div className="space-y-3 sm:space-y-4">
                  {!visibleTasks.length && (
                    <p className="text-sm text-gray-500">
                      {taskView === 'active' ? 'No active tasks right now.' : 'No pending tasks right now.'}
                    </p>
                  )}
                  {visibleTasks.map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-xl p-3 sm:p-4 hover:border-orange-200 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-3 gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <h3 className="text-gray-900 text-sm sm:text-base">{task.title}</h3>
                            {getSeverityBadge()}
                          </div>
                          <p className="text-xs sm:text-sm text-gray-600">Buyer: {task.buyerName}</p>
                          <p className="text-xs sm:text-sm text-gray-500 mt-1">
                            {task.taskType} - Goal: {task.goal}
                            {taskView === 'active' ? ` - Progress: ${task.progressed}` : ''}
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
                        <div className="flex items-center gap-2 flex-wrap">
                          <Button size="sm" variant="outline" className="rounded-full text-xs h-8" onClick={() => window.open(task.url, '_blank', 'noopener,noreferrer')}>
                            <Eye className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                            <span className="hidden sm:inline">Review</span>
                          </Button>
                          {taskView === 'pending' ? (
                            <>
                              <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white rounded-full text-xs h-8" onClick={() => handleApprove(task.id)}>
                                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                                <span className="hidden sm:inline">Approve</span>
                              </Button>
                              <Button size="sm" variant="destructive" className="rounded-full text-xs h-8" onClick={() => handleReject(task.id)}>
                                <XCircle className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                                <span className="hidden sm:inline">Reject</span>
                              </Button>
                            </>
                          ) : (
                            <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                              {task.assignedSellers || 0} Sellers Assigned
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4 sm:space-y-6">
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader className="p-4 sm:p-6">
                <CardTitle className="text-gray-900 text-base sm:text-lg">User Management</CardTitle>
                <CardDescription className="text-xs sm:text-sm">Live users from the database</CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6 pt-0">
                <Tabs defaultValue="recent" className="w-full">
                  <TabsList className="w-full mb-4">
                    <TabsTrigger value="recent" className="flex-1 text-xs sm:text-sm">Recent</TabsTrigger>
                    <TabsTrigger value="flagged" className="flex-1 text-xs sm:text-sm">Flagged</TabsTrigger>
                  </TabsList>
                  <TabsContent value="recent" className="space-y-3 sm:space-y-4">
                    <UserList users={dashboardData.recentUsers} emptyMessage="No users found" />
                  </TabsContent>
                  <TabsContent value="flagged" className="space-y-4">
                    <UserList users={dashboardData.flaggedUsers} emptyMessage="No flagged users" showReports />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
