import { DollarSign, TrendingUp, Clock, CheckCircle, Facebook, Instagram, Youtube, Twitter, Filter, LogOut, Zap, Search, ExternalLink } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

export default function SellerDashboard({ onNavigate, onLogout }) {
  const stats = [
    { label: 'Total Earnings', value: '$3,847.50', icon: DollarSign, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Tasks Completed', value: '234', icon: CheckCircle, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'In Progress', value: '8', icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Success Rate', value: '98%', icon: TrendingUp, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  const availableTasks = [
    {
      id: 1,
      title: 'Instagram Post Likes',
      platform: 'Instagram',
      type: 'Likes',
      price: 0.05,
      remaining: 158,
      total: 500,
      timeEstimate: '2 min',
      difficulty: 'Easy',
    },
    {
      id: 2,
      title: 'YouTube Video Views',
      platform: 'YouTube',
      type: 'Views',
      price: 0.08,
      remaining: 144,
      total: 1000,
      timeEstimate: '5 min',
      difficulty: 'Easy',
    },
    {
      id: 3,
      title: 'Twitter Retweets',
      platform: 'Twitter',
      type: 'Retweets',
      price: 0.12,
      remaining: 85,
      total: 200,
      timeEstimate: '1 min',
      difficulty: 'Easy',
    },
    {
      id: 4,
      title: 'Facebook Page Likes',
      platform: 'Facebook',
      type: 'Likes',
      price: 0.06,
      remaining: 45,
      total: 200,
      timeEstimate: '2 min',
      difficulty: 'Easy',
    },
    {
      id: 5,
      title: 'Instagram Story Views',
      platform: 'Instagram',
      type: 'Views',
      price: 0.04,
      remaining: 312,
      total: 500,
      timeEstimate: '1 min',
      difficulty: 'Easy',
    },
    {
      id: 6,
      title: 'YouTube Subscribe',
      platform: 'YouTube',
      type: 'Subscribe',
      price: 0.15,
      remaining: 67,
      total: 150,
      timeEstimate: '3 min',
      difficulty: 'Medium',
    },
  ];

  const myTasks = [
    {
      id: 1,
      title: 'Instagram Post Likes',
      platform: 'Instagram',
      price: 0.05,
      status: 'pending',
      submitted: '10 min ago',
      earnings: 0.05,
    },
    {
      id: 2,
      title: 'Facebook Page Likes',
      platform: 'Facebook',
      price: 0.06,
      status: 'approved',
      submitted: '2 hours ago',
      earnings: 0.06,
    },
    {
      id: 3,
      title: 'YouTube Video Views',
      platform: 'YouTube',
      price: 0.08,
      status: 'pending',
      submitted: '1 hour ago',
      earnings: 0.08,
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
    if (status === 'pending') {
      return <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">Pending</Badge>;
    }
    if (status === 'approved') {
      return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Approved</Badge>;
    }
    return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">Rejected</Badge>;
  };

  const getDifficultyBadge = (difficulty) => {
    if (difficulty === 'Easy') {
      return <Badge variant="outline" className="border-green-200 text-green-700">Easy</Badge>;
    }
    return <Badge variant="outline" className="border-orange-200 text-orange-700">Medium</Badge>;
  };

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
              <Badge className="ml-2 bg-green-100 text-green-700 hover:bg-green-100">Seller</Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => onNavigate('buyer')}>
                Switch to Buyer
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
          <h1 className="text-gray-900 mb-2">Welcome back, Sarah!</h1>
          <p className="text-gray-600">Complete tasks and earn money in your spare time.</p>
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
          {/* Available Tasks */}
          <div className="lg:col-span-2">
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-gray-900">Available Tasks</CardTitle>
                    <CardDescription>Browse and complete tasks to earn money</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input placeholder="Search tasks..." className="pl-10" />
                  </div>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="All Platforms" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Platforms</SelectItem>
                      <SelectItem value="instagram">Instagram</SelectItem>
                      <SelectItem value="facebook">Facebook</SelectItem>
                      <SelectItem value="youtube">YouTube</SelectItem>
                      <SelectItem value="twitter">Twitter</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="price-high">Highest Price</SelectItem>
                      <SelectItem value="price-low">Lowest Price</SelectItem>
                      <SelectItem value="newest">Newest</SelectItem>
                      <SelectItem value="popular">Most Popular</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Tasks List */}
                <div className="space-y-4">
                  {availableTasks.map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-xl p-4 hover:border-green-200 hover:shadow-md transition-all">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          {getPlatformIcon(task.platform)}
                          <div>
                            <h3 className="text-gray-900">{task.title}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-sm text-gray-500">{task.type}</span>
                              <span className="text-gray-300">•</span>
                              <span className="text-sm text-gray-500">{task.timeEstimate}</span>
                            </div>
                          </div>
                        </div>
                        {getDifficultyBadge(task.difficulty)}
                      </div>
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Available</span>
                          <span className="text-gray-900">
                            {task.remaining} / {task.total}
                          </span>
                        </div>
                        <Progress value={(task.remaining / task.total) * 100} className="h-2" />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-green-600">${task.price}</span>
                          <span className="text-sm text-gray-500">per task</span>
                        </div>
                        <Button className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full">
                          Start Task
                          <ExternalLink className="w-4 h-4 ml-2" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Earnings Summary */}
            <Card className="border-gray-200 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardHeader>
                <CardTitle className="text-white">Earnings Summary</CardTitle>
                <CardDescription className="text-green-100">Available for withdrawal</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-white mb-6">$3,847.50</div>
                <Button className="w-full bg-white text-green-600 hover:bg-green-50 rounded-full">
                  Withdraw Funds
                </Button>
                <div className="mt-6 pt-6 border-t border-green-400/30 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-100">This Week</span>
                    <span className="text-white">$287.50</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-100">This Month</span>
                    <span className="text-white">$1,245.00</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-100">Pending</span>
                    <span className="text-white">$124.50</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* My Tasks */}
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">My Tasks</CardTitle>
                <CardDescription>Recently submitted tasks</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="pending" className="w-full">
                  <TabsList className="w-full mb-4">
                    <TabsTrigger value="pending" className="flex-1 text-sm">Pending</TabsTrigger>
                    <TabsTrigger value="approved" className="flex-1 text-sm">Approved</TabsTrigger>
                  </TabsList>
                  <TabsContent value="pending" className="space-y-3">
                    {myTasks.filter(task => task.status === 'pending').map((task) => (
                      <div key={task.id} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex items-start gap-2 mb-2">
                          {getPlatformIcon(task.platform)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 truncate">{task.title}</p>
                            <p className="text-xs text-gray-500">{task.submitted}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-green-600">${task.earnings.toFixed(2)}</span>
                          {getStatusBadge(task.status)}
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                  <TabsContent value="approved" className="space-y-3">
                    {myTasks.filter(task => task.status === 'approved').map((task) => (
                      <div key={task.id} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex items-start gap-2 mb-2">
                          {getPlatformIcon(task.platform)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 truncate">{task.title}</p>
                            <p className="text-xs text-gray-500">{task.submitted}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-green-600">${task.earnings.toFixed(2)}</span>
                          {getStatusBadge(task.status)}
                        </div>
                      </div>
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Performance Stats */}
            <Card className="border-gray-200 rounded-2xl">
              <CardHeader>
                <CardTitle className="text-gray-900">Performance</CardTitle>
                <CardDescription>Last 30 days</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Approval Rate</span>
                  <span className="text-green-600">98%</span>
                </div>
                <Progress value={98} className="h-2" />
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg. Completion Time</span>
                  <span className="text-gray-900">3.2 min</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Tasks Completed</span>
                  <span className="text-gray-900">87</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Streak</span>
                  <span className="text-orange-600">🔥 12 days</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}