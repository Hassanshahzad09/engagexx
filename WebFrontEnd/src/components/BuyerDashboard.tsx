import { useState } from 'react';
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
import { useLocation } from 'react-router-dom';
export default function BuyerDashboard({ onNavigate, onLogout }) {
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);

  const stats = [
    { label: 'Wallet Balance', value: '$2,450.00', icon: Wallet, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Active Tasks', value: '12', icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Completed Tasks', value: '48', icon: CheckCircle, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'Total Engagement', value: '15.2K', icon: TrendingUp, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  const tasks = [
    {
      id: 1,
      title: 'Instagram Post Likes',
      platform: 'Instagram',
      type: 'Likes',
      target: 500,
      completed: 342,
      price: 0.05,
      status: 'active',
      created: '2 hours ago',
    },
    {
      id: 2,
      title: 'YouTube Video Views',
      platform: 'YouTube',
      type: 'Views',
      target: 1000,
      completed: 856,
      price: 0.08,
      status: 'active',
      created: '5 hours ago',
    },
    {
      id: 3,
      title: 'Facebook Page Likes',
      platform: 'Facebook',
      type: 'Likes',
      target: 200,
      completed: 200,
      price: 0.06,
      status: 'completed',
      created: '1 day ago',
    },
    {
      id: 4,
      title: 'Twitter Followers',
      platform: 'Twitter',
      type: 'Follows',
      target: 300,
      completed: 145,
      price: 0.10,
      status: 'active',
      created: '3 hours ago',
    },
  ];

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'Instagram':
        return <Instagram className="w-5 h-5 text-pink-600" />;
      case 'YouTube':
        return <Youtube className="w-5 h-5 text-red-600" />;
      case 'Facebook':
        return <Facebook className="w-5 h-5 text-blue-600" />;
      case 'Twitter':
        return <Twitter className="w-5 h-5 text-sky-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'active') {
      return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">Active</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Completed</Badge>;
  };

  const location = useLocation()
  const user = location.state?.userData;
  console.log("user data : ",user)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
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
              <Button variant="ghost" size="sm" onClick={() => onNavigate('seller')}>
                Switch to Seller
              </Button>
              <Button variant="ghost" size="sm" onClick={onLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">Welcome back, John!</h1>
          <p className="text-gray-600">Manage your social media engagement tasks and track performance.</p>
        </div>

        {/* Stats Grid */}
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

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Tasks List */}
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
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="platform">Platform</Label>
                            <Select>
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
                            <Select>
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
                          <Input id="url" placeholder="https://..." />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="target">Target Count</Label>
                            <Input id="target" type="number" placeholder="500" />
                          </div>
                          <div>
                            <Label htmlFor="price">Price per Action ($)</Label>
                            <Input id="price" type="number" step="0.01" placeholder="0.05" />
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
                              <p className="text-green-700">$25.00 (500 actions × $0.05)</p>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-3 pt-4">
                          <Button
                            className="flex-1 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                            onClick={() => setIsCreateTaskOpen(false)}
                          >
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
                    {tasks.filter(task => task.status === 'active').map((task) => (
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
                            <span className="text-gray-900">
                              {task.completed} / {task.target}
                            </span>
                          </div>
                          <Progress value={(task.completed / task.target) * 100} className="h-2" />
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-gray-600">
                            Price: <span className="text-green-600">${task.price}</span> per {task.type.toLowerCase()}
                          </div>
                          <Button variant="outline" size="sm" className="rounded-full">
                            View Details
                          </Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  <TabsContent value="completed" className="space-y-4">
                    {tasks.filter(task => task.status === 'completed').map((task) => (
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
                          <div className="text-sm text-gray-600">
                            Total: <span className="text-gray-900">${(task.target * task.price).toFixed(2)}</span>
                          </div>
                          <Button variant="outline" size="sm" className="rounded-full">
                            View Report
                          </Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  <TabsContent value="all" className="space-y-4">
                    {tasks.map((task) => (
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
                        {task.status === 'active' && (
                          <div className="space-y-2 mb-4">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Progress</span>
                              <span className="text-gray-900">
                                {task.completed} / {task.target}
                              </span>
                            </div>
                            <Progress value={(task.completed / task.target) * 100} className="h-2" />
                          </div>
                        )}
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-gray-600">
                            {task.status === 'active' ? (
                              <>Price: <span className="text-green-600">${task.price}</span> per {task.type.toLowerCase()}</>
                            ) : (
                              <>Total: <span className="text-gray-900">${(task.target * task.price).toFixed(2)}</span></>
                            )}
                          </div>
                          <Button variant="outline" size="sm" className="rounded-full">
                            {task.status === 'active' ? 'View Details' : 'View Report'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full">
                  <Wallet className="w-4 h-4 mr-2" />
                  Add Funds
                </Button>
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

            {/* Performance Overview */}
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">Performance</CardTitle>
                <CardDescription>Last 30 days</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Task Success Rate</span>
                  <span className="text-green-600">94%</span>
                </div>
                <Progress value={94} className="h-2" />
                
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
                  <span className="text-gray-900">12</span>
                </div>
              </CardContent>
            </Card>

            {/* Platform Distribution */}
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">Platform Usage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3">
                  <Instagram className="w-5 h-5 text-pink-600" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Instagram</span>
                      <span className="text-sm text-gray-900">45%</span>
                    </div>
                    <Progress value={45} className="h-1.5" />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Youtube className="w-5 h-5 text-red-600" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">YouTube</span>
                      <span className="text-sm text-gray-900">30%</span>
                    </div>
                    <Progress value={30} className="h-1.5" />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Facebook className="w-5 h-5 text-blue-600" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Facebook</span>
                      <span className="text-sm text-gray-900">15%</span>
                    </div>
                    <Progress value={15} className="h-1.5" />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Twitter className="w-5 h-5 text-sky-600" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Twitter</span>
                      <span className="text-sm text-gray-900">10%</span>
                    </div>
                    <Progress value={10} className="h-1.5" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}