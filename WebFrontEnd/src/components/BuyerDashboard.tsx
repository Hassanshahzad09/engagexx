import { useEffect, useMemo, useState } from 'react';
import { Plus, Wallet, TrendingUp, Clock, CheckCircle, Facebook, Instagram, Youtube, Twitter, BarChart3, Filter, LogOut, Zap, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useLocation, useNavigate } from 'react-router-dom';

export default function BuyerDashboard({ onLogout }) {
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [isAddFundsOpen, setIsAddFundsOpen] = useState(false);
  const [fundAmount, setFundAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('jazzcash');
  const [walletBalance, setWalletBalance] = useState(0);
  const [taskForm, setTaskForm] = useState({
    title: '',
    platform: '', 
    taskType: '',
    url: '',
    goal: '',
    pricePerAction: '',
  });
  const [dashboardStats, setDashboardStats] = useState({
    activeTasks: 0,
    completedTasks: 0,
    allTasks: 0,
    totalEngagement: 0,
    performance: 0,
    tasks: [],
  });

  const location = useLocation();
  const navigate = useNavigate();
  const user = location.state?.userData;
  const loggedInUserName = user?.userName || 'Buyer';
  const estimatedCost = useMemo(() => {
    const target = Number(taskForm.goal) || 0;
    const price = Number(taskForm.pricePerAction) || 0;
    return (target * price).toFixed(2);
  }, [taskForm.goal, taskForm.pricePerAction]);
  const handleLogout = () => {
    if (typeof onLogout === 'function') {
      onLogout();
      return;
    }
    navigate('/');
  };
//console.log(user)
  useEffect(() => {
    if (!user?.userId) return;

    const fetchDashboardStats = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/buyer-dashboard-stats/${user.userId}/`);
        const data = await response.json();

        if (response.ok) {
          setDashboardStats({
            activeTasks: data.activeTasks || 0,
            completedTasks: data.completedTasks || 0,
            allTasks: data.allTasks || 0,
            totalEngagement: data.totalEngagement || 0,
            performance: data.performance || 0,
            tasks: data.tasks || [],
          });
        }
      } catch (error) {
        console.error('Dashboard stats error:', error);
      }
    };

    const fetchWalletBalance = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/wallet-balance/${user.userId}/`);
        const data = await response.json();

        if (response.ok) {
          setWalletBalance(Number(data.walletBalance) || 0);
        }
      } catch (error) {
        console.error('Wallet balance fetch error:', error);
      }
    };

    fetchDashboardStats();
    fetchWalletBalance();
  }, [user]);

  const stats = [
    { label: 'Wallet Balance', value: `$${walletBalance.toFixed(2)}`, icon: Wallet, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Active Tasks', value: dashboardStats.activeTasks, icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Completed Tasks', value: dashboardStats.completedTasks, icon: CheckCircle, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'Platform Usage', value: dashboardStats.totalEngagement, icon: TrendingUp, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'Instagram':
      case 'instagram':
        return <Instagram className="w-5 h-5 text-pink-600" />;
      case 'YouTube':
      case 'youtube':
        return <Youtube className="w-5 h-5 text-red-600" />;
      case 'Facebook':
      case 'facebook':
        return <Facebook className="w-5 h-5 text-blue-600" />;
      case 'Twitter':
      case 'twitter':
        return <Twitter className="w-5 h-5 text-sky-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'active' || status === 'in_progress') {
      return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">Active</Badge>;
    }
    if (status === 'pending') {
      return <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">Pending</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Completed</Badge>;
  };

  const handleCreateTask = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/create-task/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user.userId,
          title: taskForm.title,
          platform: taskForm.platform,
          taskType: taskForm.taskType,
          url: taskForm.url,
          goal: taskForm.goal,
          pricePerAction: taskForm.pricePerAction,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        setIsCreateTaskOpen(false);
        window.location.reload();
      } else {
        alert(data.error || 'Task creation failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  const handleAddFunds = async () => {
    try {
      const amount = Number(fundAmount);
      if (!amount || amount <= 0) {
        alert('Enter a valid amount');
        return;
      }

      const response = await fetch('http://127.0.0.1:8000/api/add-funds/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user.userId,
          amount,
          paymentMethod,
          description: 'Buyer wallet top up',
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setWalletBalance(Number(data.walletBalance) || 0);
        setFundAmount('');
        setIsAddFundsOpen(false);
        alert(data.message || 'Funds added successfully');
      } else {
        alert(data.error || 'Add funds failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <span className="text-gray-900">Engage X</span>
              <Badge className="ml-2 bg-blue-100 text-blue-700 hover:bg-blue-100">Buyer</Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">Welcome back, {loggedInUserName}!</h1>
          <p className="text-gray-600">Manage your social media engagement tasks and track performance.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="border-gray-200 rounded-2xl hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                    <p className="text-gray-900">{stat.value}</p>
                  </div>
                  <div className={`w-12 h-12 ${stat.bg} rounded-xl flex items-center justify-center`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-gray-900">Your Tasks</CardTitle>
                    <CardDescription>Monitor and manage your engagement tasks</CardDescription>
                  </div>
                  <Dialog open={isCreateTaskOpen} onOpenChange={setIsCreateTaskOpen}>
                    <DialogTrigger asChild>
                      <Button className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full">
                        <Plus className="w-4 h-4 mr-2" />
                        Create Task
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Create New Task</DialogTitle>
                        <DialogDescription>Fill in the details to create a new engagement task</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 pt-4">
                        <div>
                          <Label htmlFor="title">Task Title</Label>
                          <Input id="title" placeholder="Instagram Post Likes" value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="platform">Platform</Label>
                            <Select onValueChange={(value) => setTaskForm({ ...taskForm, platform: value })}>
                              <SelectTrigger id="platform">
                                <SelectValue placeholder="Select platform" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="instagram">Instagram</SelectItem>
                                <SelectItem value="facebook">Facebook</SelectItem>
                                <SelectItem value="youtube">YouTube</SelectItem>
                                <SelectItem value="twitter">Twitter</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label htmlFor="task-type">Task Type</Label>
                            <Select onValueChange={(value) => setTaskForm({ ...taskForm, taskType: value })}>
                              <SelectTrigger id="task-type">
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="likes">Likes</SelectItem>
                                <SelectItem value="follows">Follows</SelectItem>
                                <SelectItem value="views">Views</SelectItem>
                                <SelectItem value="comments">Comments</SelectItem>
                                <SelectItem value="shares">Shares</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="url">Post/Profile URL</Label>
                          <Input id="url" placeholder="https://..." value={taskForm.url} onChange={(e) => setTaskForm({ ...taskForm, url: e.target.value })} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="target">Target Count</Label>
                            <Input id="target" type="number" placeholder="500" value={taskForm.goal} onChange={(e) => setTaskForm({ ...taskForm, goal: e.target.value })} />
                          </div>
                          <div>
                            <Label htmlFor="price">Price per Action ($)</Label>
                            <Input id="price" type="number" step="0.01" placeholder="0.05" value={taskForm.pricePerAction} onChange={(e) => setTaskForm({ ...taskForm, pricePerAction: e.target.value })} />
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="instructions">Special Instructions (Optional)</Label>
                          <Textarea id="instructions" placeholder="Any specific requirements..." rows={3} />
                        </div>
                        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                          <div className="flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-green-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-green-900 mb-1">Estimated Cost</p>
                              <p className="text-green-700">
                                ${estimatedCost} ({taskForm.goal || 0} actions x ${taskForm.pricePerAction || 0})
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-3 pt-4">
                          <Button className="flex-1 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full" onClick={handleCreateTask}>
                            Create Task
                          </Button>
                          <Button variant="outline" className="flex-1 rounded-full" onClick={() => setIsCreateTaskOpen(false)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="active" className="w-full">
                  <TabsList className="w-full mb-6">
                    <TabsTrigger value="active" className="flex-1">Active</TabsTrigger>
                    <TabsTrigger value="completed" className="flex-1">Completed</TabsTrigger>
                    <TabsTrigger value="all" className="flex-1">All Tasks</TabsTrigger>
                  </TabsList>
                  <TabsContent value="active" className="space-y-4">
                    {dashboardStats.tasks.filter((task) => task.status === 'active' || task.status === 'in_progress').map((task) => (
                      <div key={task.id} className="border border-gray-200 rounded-xl p-4 hover:border-green-200 transition-colors">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getPlatformIcon(task.platform)}
                            <div>
                              <h3 className="text-gray-900">{task.title}</h3>
                              <p className="text-sm text-gray-500">{task.created}</p>
                            </div>
                          </div>
                          {getStatusBadge(task.status)}
                        </div>
                        <div className="space-y-2 mb-4">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">Progress</span>
                            <span className="text-gray-900">{task.completed} / {task.target}</span>
                          </div>
                          <Progress value={task.target ? (task.completed / task.target) * 100 : 0} className="h-2" />
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-gray-600">Price: <span className="text-green-600">${task.price}</span> per {String(task.type).toLowerCase()}</div>
                          <Button variant="outline" size="sm" className="rounded-full">View Details</Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  <TabsContent value="completed" className="space-y-4">
                    {dashboardStats.tasks.filter((task) => task.status === 'completed').map((task) => (
                      <div key={task.id} className="border border-gray-200 rounded-xl p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getPlatformIcon(task.platform)}
                            <div>
                              <h3 className="text-gray-900">{task.title}</h3>
                              <p className="text-sm text-gray-500">{task.created}</p>
                            </div>
                          </div>
                          {getStatusBadge(task.status)}
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-gray-600">Total: <span className="text-gray-900">${(task.target * task.price).toFixed(2)}</span></div>
                          <Button variant="outline" size="sm" className="rounded-full">View Report</Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  <TabsContent value="all" className="space-y-4">
                    {dashboardStats.tasks.map((task) => (
                      <div key={task.id} className="border border-gray-200 rounded-xl p-4 hover:border-green-200 transition-colors">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getPlatformIcon(task.platform)}
                            <div>
                              <h3 className="text-gray-900">{task.title}</h3>
                              <p className="text-sm text-gray-500">{task.created}</p>
                            </div>
                          </div>
                          {getStatusBadge(task.status)}
                        </div>
                        {(task.status === 'active' || task.status === 'in_progress') && (
                          <div className="space-y-2 mb-4">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Progress</span>
                              <span className="text-gray-900">{task.completed} / {task.target}</span>
                            </div>
                            <Progress value={task.target ? (task.completed / task.target) * 100 : 0} className="h-2" />
                          </div>
                        )}
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-gray-600">
                            {(task.status === 'active' || task.status === 'in_progress') ? (
                              <>Price: <span className="text-green-600">${task.price}</span> per {String(task.type).toLowerCase()}</>
                            ) : (
                              <>Total: <span className="text-gray-900">${(task.target * task.price).toFixed(2)}</span></>
                            )}
                          </div>
                          <Button variant="outline" size="sm" className="rounded-full">
                            {(task.status === 'active' || task.status === 'in_progress') ? 'View Details' : 'View Report'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
              <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Dialog open={isAddFundsOpen} onOpenChange={setIsAddFundsOpen}>
                  <DialogTrigger asChild>
                    <Button className="w-full justify-start bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full">
                      <Wallet className="w-4 h-4 mr-2" />
                      Add Funds
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle>Add Funds</DialogTitle>
                      <DialogDescription>Top up your buyer wallet balance</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label htmlFor="fundAmount">Amount</Label>
                      <Input
                        id="fundAmount"
                        type="number"
                          step="0.01"
                          min="1"
                          placeholder="Enter amount"
                        value={fundAmount}
                        onChange={(e) => setFundAmount(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="paymentMethod">Payment Method</Label>
                      <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                        <SelectTrigger id="paymentMethod">
                          <SelectValue placeholder="Choose payment method" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="jazzcash">JazzCash</SelectItem>
                          <SelectItem value="easypaisa">Easypaisa</SelectItem>
                          <SelectItem value="card">Debit/Credit Card</SelectItem>
                          <SelectItem value="manual">Manual / Test Top Up</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                      <div className="flex gap-3 pt-2">
                        <Button
                          className="flex-1 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                          onClick={handleAddFunds}
                        >
                          Add Funds
                        </Button>
                        <Button variant="outline" className="flex-1 rounded-full" onClick={() => setIsAddFundsOpen(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
                <Button variant="outline" className="w-full justify-start rounded-full">
                  <BarChart3 className="w-4 h-4 mr-2" />
                  View Analytics
                </Button>
                <Button variant="outline" className="w-full justify-start rounded-full">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter Tasks
                </Button>
              </CardContent>
            </Card>

            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">Performance</CardTitle>
                <CardDescription>Last 30 days</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Task Success Rate</span>
                  <span className="text-green-600">{dashboardStats.performance}%</span>
                </div>
                <Progress value={dashboardStats.performance} className="h-2" />

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg. Completion Time</span>
                  <span className="text-gray-900">2.5 days</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Spent</span>
                  <span className="text-gray-900">$1,284</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Active Campaigns</span>
                  <span className="text-gray-900">{dashboardStats.activeTasks || 0}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
