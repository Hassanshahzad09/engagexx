import { DollarSign, TrendingUp, Clock, CheckCircle, Facebook, Instagram, Youtube, Twitter, LogOut, Zap, Search, ExternalLink, Play, Pause, StopCircle, Upload } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { useState, useEffect } from 'react';

export default function SellerDashboard({ onNavigate, onLogout }) {
  const STORAGE_KEY = 'engageXUser';
  const [availableTasks, setAvailableTasks] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false);
  const [timer, setTimer] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [proofUrl, setProofUrl] = useState('');
  const [notes, setNotes] = useState('');

  // Fetch approved tasks from API (from old code)
  useEffect(() => {
    const fetchApprovedTasks = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/approved-tasks/');
        const data = await response.json();
        if (response.ok) {
          setAvailableTasks(data.tasks || []);
        }
      } catch (error) {
        console.error('Approved tasks fetch error:', error);
      }
    };
    fetchApprovedTasks();
  }, []);

  // Timer effect
  useEffect(() => {
    let interval;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setTimer((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartTask = (task) => {
    setActiveTask(task);
    setIsTaskDialogOpen(true);
    setTimer(0);
    setIsTimerRunning(true);
    setProofUrl('');
    setNotes('');
  };

  const handlePauseTimer = () => {
    setIsTimerRunning(!isTimerRunning);
  };

  const handleStopTask = () => {
    setIsTimerRunning(false);
  };

  const handleSubmitTask = async () => {
    try {
      // Submit task proof to API
      const response = await fetch('http://127.0.0.1:8000/api/submit-task/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: activeTask?.id,
          proof_url: proofUrl,
          notes: notes,
          time_spent: timer,
        }),
      });
      if (!response.ok) {
        console.error('Submit task failed');
      }
    } catch (error) {
      console.error('Submit task error:', error);
    }
    setIsTaskDialogOpen(false);
    setActiveTask(null);
    setTimer(0);
    setIsTimerRunning(false);
    setProofUrl('');
    setNotes('');
  };

  const getPlatformUrl = (platform, type) => {
    // Use the task's actual URL if provided by API, fallback to mocks
    if (activeTask?.url) return activeTask.url;
    const urls = {
      Instagram: 'https://www.instagram.com',
      instagram: 'https://www.instagram.com',
      YouTube: 'https://www.youtube.com',
      youtube: 'https://www.youtube.com',
      Facebook: 'https://www.facebook.com',
      facebook: 'https://www.facebook.com',
      Twitter: 'https://www.twitter.com',
      twitter: 'https://www.twitter.com',
    };
    return urls[platform] || 'https://www.google.com';
  };

  const stats = [
    { label: 'Total Earnings', value: '$3,847.50', icon: DollarSign, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Tasks Completed', value: '234', icon: CheckCircle, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'In Progress', value: '8', icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Success Rate', value: '98%', icon: TrendingUp, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  const myTasks = [
    { id: 1, title: 'Instagram Post Likes', platform: 'Instagram', price: 0.05, status: 'pending', submitted: '10 min ago', earnings: 0.05 },
    { id: 2, title: 'Facebook Page Likes', platform: 'Facebook', price: 0.06, status: 'approved', submitted: '2 hours ago', earnings: 0.06 },
    { id: 3, title: 'YouTube Video Views', platform: 'YouTube', price: 0.08, status: 'pending', submitted: '1 hour ago', earnings: 0.08 },
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

  const handleLogoutClick = () => {
    localStorage.removeItem(STORAGE_KEY);

    if (onLogout) {
      onLogout();
      return;
    }

    window.location.href = '/';
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
              <Button variant="ghost" size="sm" onClick={handleLogoutClick}>
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">Welcome back, Sarah!</h1>
          <p className="text-gray-600">Complete tasks and earn money in your spare time.</p>
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
                <CardTitle className="text-gray-900">Available Tasks</CardTitle>
                <CardDescription>Browse and complete tasks to earn money</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input placeholder="Search tasks..." className="pl-10" />
                  </div>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="All Platforms" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Platforms</SelectItem>
                      <SelectItem value="instagram">Instagram</SelectItem>
                      <SelectItem value="facebook">Facebook</SelectItem>
                      <SelectItem value="youtube">YouTube</SelectItem>
                      <SelectItem value="twitter">Twitter</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Sort by" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="price-high">Highest Price</SelectItem>
                      <SelectItem value="price-low">Lowest Price</SelectItem>
                      <SelectItem value="newest">Newest</SelectItem>
                      <SelectItem value="popular">Most Popular</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-4">
                  {availableTasks.length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-8">No tasks available right now.</p>
                  )}
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
                          <span className="text-gray-900">{task.remaining} / {task.total}</span>
                        </div>
                        <Progress value={task.total ? (task.remaining / task.total) * 100 : 0} className="h-2" />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-green-600">${task.price}</span>
                          <span className="text-sm text-gray-500">per task</span>
                        </div>
                        <Button
                          className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                          onClick={() => handleStartTask(task)}
                        >
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

          <div className="space-y-6">
            <Card className="border-gray-200 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardHeader>
                <CardTitle className="text-white">Earnings Summary</CardTitle>
                <CardDescription className="text-green-100">Available for withdrawal</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-white mb-6">$3,847.50</div>
                <Button className="w-full bg-white text-green-600 hover:bg-green-50 rounded-full">Withdraw Funds</Button>
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
                    {myTasks.filter((task) => task.status === 'pending').map((task) => (
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
                    {myTasks.filter((task) => task.status === 'approved').map((task) => (
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

      {/* Task Dialog */}
      <Dialog open={isTaskDialogOpen} onOpenChange={setIsTaskDialogOpen}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Complete Task</DialogTitle>
            <DialogDescription>Perform the task on the platform and submit your proof.</DialogDescription>
          </DialogHeader>

          {activeTask && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-3">
                  {getPlatformIcon(activeTask.platform)}
                  <div>
                    <h3 className="text-gray-900 font-medium">{activeTask.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm text-gray-500">{activeTask.type}</span>
                      <span className="text-gray-300">•</span>
                      <span className="text-sm text-green-600 font-medium">${activeTask.price} per task</span>
                    </div>
                  </div>
                </div>
                {getDifficultyBadge(activeTask.difficulty)}
              </div>

              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-xl">
                <div className="flex items-center gap-3">
                  <Button size="sm" variant="outline" onClick={handlePauseTimer} className="rounded-full">
                    {isTimerRunning ? (<><Pause className="w-4 h-4 mr-1" /> Pause</>) : (<><Play className="w-4 h-4 mr-1" /> Resume</>)}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleStopTask} className="rounded-full text-red-600 border-red-200 hover:bg-red-50">
                    <StopCircle className="w-4 h-4 mr-1" />Stop
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-green-600" />
                  <span className="text-2xl font-mono font-bold text-gray-900">{formatTime(timer)}</span>
                </div>
              </div>

              <div className="border-2 border-gray-200 rounded-xl overflow-hidden">
                <div className="bg-gray-100 px-4 py-2 flex items-center justify-between border-b border-gray-200">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    {getPlatformIcon(activeTask.platform)}
                    <span className="font-medium">{activeTask.platform}</span>
                  </span>
                  <a
                    href={getPlatformUrl(activeTask.platform, activeTask.type)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
                  >
                    Open in New Tab<ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <iframe
                  src={getPlatformUrl(activeTask.platform, activeTask.type)}
                  className="w-full h-[400px]"
                  title={`${activeTask.platform} Task`}
                  sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Instructions:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Complete the {activeTask.type} action on the platform above</li>
                  <li>• Take a screenshot or copy the URL as proof</li>
                  <li>• Paste the proof URL in the field below</li>
                  <li>• Add any additional notes if needed</li>
                  <li>• Click "Submit Task" when complete</li>
                </ul>
              </div>

              <div className="space-y-4 pt-2">
                <div className="space-y-2">
                  <Label htmlFor="proofUrl" className="text-sm font-medium">Proof URL / Screenshot Link *</Label>
                  <Input
                    id="proofUrl"
                    value={proofUrl}
                    onChange={(e) => setProofUrl(e.target.value)}
                    placeholder="https://imgur.com/screenshot or profile URL"
                    className="border-gray-300"
                  />
                  <p className="text-xs text-gray-500">Provide a link to your screenshot (e.g., Imgur, Google Drive) or the profile/post URL</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes" className="text-sm font-medium">Additional Notes (Optional)</Label>
                  <Textarea
                    id="notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add any relevant information about the completed task..."
                    rows={3}
                    className="border-gray-300"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4 border-t">
                <Button
                  className="flex-1 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                  onClick={handleSubmitTask}
                  disabled={!proofUrl}
                >
                  <Upload className="w-4 h-4 mr-2" />Submit Task
                </Button>
                <Button variant="outline" className="rounded-full" onClick={() => setIsTaskDialogOpen(false)}>Cancel</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
