import { useEffect, useState } from 'react';
import { Users, DollarSign, AlertTriangle, TrendingUp, CheckCircle, XCircle, Eye, Ban, LogOut, Zap } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminDashboard({ onNavigate, onLogout }) {
  const [pendingTasks, setPendingTasks] = useState([]);

  const stats = [
    { label: 'Total Users', value: '12,458', change: '+12.5%', icon: Users, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Revenue', value: '$45,892', change: '+8.2%', icon: DollarSign, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Active Tasks', value: '1,284', change: '+15.3%', icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'Pending Tasks', value: pendingTasks.length, change: 'Needs review', icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  const revenueData = [
    { name: 'Jan', revenue: 24500, users: 245 },
    { name: 'Feb', revenue: 28200, users: 298 },
    { name: 'Mar', revenue: 31800, users: 342 },
    { name: 'Apr', revenue: 35400, users: 389 },
    { name: 'May', revenue: 38900, users: 425 },
    { name: 'Jun', revenue: 42300, users: 468 },
    { name: 'Jul', revenue: 45892, users: 512 },
  ];

  const taskDistribution = [
    { name: 'Instagram', value: 450 },
    { name: 'YouTube', value: 380 },
    { name: 'Facebook', value: 290 },
    { name: 'Twitter', value: 164 },
  ];

  const recentUsers = [
    { id: 1, name: 'Alice Johnson', email: 'alice@example.com', type: 'Buyer', status: 'Active', joined: '2 days ago' },
    { id: 2, name: 'Bob Williams', email: 'bob@example.com', type: 'Seller', status: 'Active', joined: '3 days ago' },
    { id: 3, name: 'Carol Brown', email: 'carol@example.com', type: 'Buyer', status: 'Suspended', joined: '5 days ago' },
    { id: 4, name: 'David Lee', email: 'david@example.com', type: 'Seller', status: 'Active', joined: '1 week ago' },
  ];

  const fetchPendingTasks = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/admin-pending-tasks/');
      const data = await response.json();
      if (response.ok) {
        setPendingTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('Pending tasks fetch error:', error);
    }
  };

  const handleApprove = async (taskId) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/approve-task/${taskId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        fetchPendingTasks();
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
        fetchPendingTasks();
      } else {
        alert(data.error || 'Reject failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  useEffect(() => {
    fetchPendingTasks();
  }, []);

  const getSeverityBadge = () => {
    return <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">Pending</Badge>;
  };

  const getUserTypeBadge = (type) => {
    if (type === 'Buyer') {
      return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">Buyer</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Seller</Badge>;
  };

  const getStatusBadge = (status) => {
    if (status === 'Active') {
      return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Active</Badge>;
    }
    return <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-100">Suspended</Badge>;
  };

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
              <Button variant="ghost" size="sm" onClick={onLogout} className="text-xs sm:text-sm">
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
          <p className="text-gray-600 text-sm sm:text-base">Monitor platform activity and manage users and tasks.</p>
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
              <CardTitle className="text-gray-900 text-base sm:text-lg">Revenue Overview</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Monthly revenue and user growth</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={revenueData}>
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
            </CardContent>
          </Card>

          <Card className="border-gray-200 rounded-2xl">
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-gray-900 text-base sm:text-lg">Task Distribution</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Tasks by platform</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={taskDistribution}>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8">
          <div className="lg:col-span-2">
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader className="p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <CardTitle className="text-gray-900 text-base sm:text-lg">Pending Tasks</CardTitle>
                    <CardDescription className="text-xs sm:text-sm">Review buyer tasks before they go live on the portal</CardDescription>
                  </div>
                  <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100 w-fit text-xs sm:text-sm">{pendingTasks.length} Pending</Badge>
                </div>
              </CardHeader>
              <CardContent className="p-4 sm:p-6 pt-0">
                <div className="space-y-3 sm:space-y-4">
                  {pendingTasks.map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-xl p-3 sm:p-4 hover:border-orange-200 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-3 gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <h3 className="text-gray-900 text-sm sm:text-base">{task.title}</h3>
                            {getSeverityBadge()}
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
                          <Button size="sm" variant="outline" className="rounded-full text-xs h-8">
                            <Eye className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                            <span className="hidden sm:inline">Review</span>
                          </Button>
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
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4 sm:space-y-6">
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader className="p-4 sm:p-6">
                <CardTitle className="text-gray-900 text-base sm:text-lg">User Management</CardTitle>
                <CardDescription className="text-xs sm:text-sm">Recent user activity</CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6 pt-0">
                <Tabs defaultValue="recent" className="w-full">
                  <TabsList className="w-full mb-4">
                    <TabsTrigger value="recent" className="flex-1 text-xs sm:text-sm">Recent</TabsTrigger>
                    <TabsTrigger value="flagged" className="flex-1 text-xs sm:text-sm">Flagged</TabsTrigger>
                  </TabsList>
                  <TabsContent value="recent" className="space-y-3 sm:space-y-4">
                    {recentUsers.map((user) => (
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
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>Joined {user.joined}</span>
                          <Button size="sm" variant="ghost" className="h-6 px-2">
                            <Ban className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  <TabsContent value="flagged" className="space-y-4">
                    <div className="text-center py-8 text-gray-500">
                      <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-xs sm:text-sm">No flagged users</p>
                    </div>
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
