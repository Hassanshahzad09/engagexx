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
import { useState, useEffect, useRef } from 'react';
import type { MouseEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ConnectSocial from './ConnectSocial';

interface YouTubeDrawerProps {
  videoUrl: string;
  onClose: () => void;
  onComplete: (timeSpentSeconds: number) => void;
}

function YouTubeDrawer({ videoUrl, onClose, onComplete }: YouTubeDrawerProps) {
  const [animIn, setAnimIn] = useState(false);
  const [watchPercent, setWatchPercent] = useState(0);
  const [player, setPlayer] = useState<any>(null);
  const [isComplete, setIsComplete] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const getVideoId = (url: string): string | null => {
    const patterns = [
      /youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})/,
      /youtu\.be\/([a-zA-Z0-9_-]{11})/,
      /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }

    return null;
  };

  const videoId = getVideoId(videoUrl);

  useEffect(() => {
    if (!videoId) return;

    requestAnimationFrame(() => setTimeout(() => setAnimIn(true), 10));

    if (!(window as any).YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      if (firstScriptTag?.parentNode) {
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
      } else {
        document.head.appendChild(tag);
      }
    }

    const onReady = () => {
      const yt = (window as any).YT;
      if (yt && yt.Player) {
        const newPlayer = new yt.Player('youtube-player', {
          videoId,
          events: {
            onStateChange: (event: any) => {
              if (event.data === yt.PlayerState.PLAYING) {
                const checkProgress = setInterval(() => {
                  if (newPlayer && newPlayer.getCurrentTime && newPlayer.getDuration) {
                    const current = newPlayer.getCurrentTime();
                    const duration = newPlayer.getDuration();

                    if (duration > 0) {
                      const percent = (current / duration) * 100;
                      setWatchPercent(percent);

                      if (percent >= 70 && !isComplete) {
                        setIsComplete(true);
                        onComplete(Math.floor(current));
                        clearInterval(checkProgress);
                      }
                    }
                  }
                }, 1000);

                (newPlayer as any)._progressInterval = checkProgress;
              } else if ((newPlayer as any)._progressInterval) {
                clearInterval((newPlayer as any)._progressInterval);
              }
            },
          },
        });

        setPlayer(newPlayer);
      }
    };

    if ((window as any).YT && (window as any).YT.Player) {
      onReady();
    } else {
      (window as any).onYouTubeIframeAPIReady = onReady;
    }

    return () => {
      if (player && (player as any)._progressInterval) {
        clearInterval((player as any)._progressInterval);
      }
    };
  }, [videoId]);

  const closeDrawer = () => {
    if (!isComplete) return;
    setAnimIn(false);
    setTimeout(() => onClose(), 350);
  };

  const handleBackdropClick = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && isComplete) {
      closeDrawer();
    }
  };

  if (!videoId) {
    return (
      <div style={styles.backdrop} onClick={handleBackdropClick}>
        <div style={styles.drawer}>
          <div style={styles.handle} />
          <div style={{ padding: 20, textAlign: 'center', color: 'red' }}>
            Invalid YouTube URL.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        ...styles.backdrop,
        opacity: animIn ? 1 : 0,
        transition: 'opacity 0.3s ease',
        alignItems: 'flex-end',
      }}
      onClick={handleBackdropClick}
    >
      <div
        style={{
          ...styles.drawer,
          transform: animIn ? 'translateY(0)' : 'translateY(100%)',
          transition: 'transform 0.35s cubic-bezier(0.4,0,0.2,1)',
        }}
        onClick={(event) => event.stopPropagation()}
      >
        <div style={styles.handle} />

        <div style={styles.drawerHeader}>
          <div style={styles.platformBadge}>
            <div style={styles.platformIcon}>
              <Youtube className="w-5 h-5 text-red-600" />
            </div>
            <span style={styles.platformName}>YouTube Task</span>
          </div>
          {isComplete ? (
            <button style={styles.closeBtn} onClick={closeDrawer}>x</button>
          ) : (
            <div style={{ width: 32, height: 32 }} />
          )}
        </div>

        <div style={styles.drawerBody}>
          <div style={{ width: '100%', aspectRatio: '16/9', borderRadius: 12, overflow: 'hidden', background: '#000' }}>
            <div id="youtube-player" style={{ width: '100%', height: '100%' }} />
          </div>
          <div style={{ marginTop: 16, textAlign: 'center', color: '#666' }}>
            {!isComplete ? (
              <div>
                <Progress value={watchPercent} className="h-2 mb-2" style={{ maxWidth: 300, margin: '0 auto' }} />
                <p className="text-sm">Watch at least 70% to unlock close button</p>
                <p className="text-xs text-gray-400 mt-1">Current: {Math.floor(watchPercent)}%</p>
              </div>
            ) : (
              <p className="text-green-600 text-sm">Video requirement met. You may close this drawer.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SellerDashboard({ userData, onLogout, theme = 'light' }) {
  const [availableTasks, setAvailableTasks] = useState<any[]>([]);
  const [activeTask, setActiveTask] = useState<any | null>(null);
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false);
  const [timer, setTimer] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [proofUrl, setProofUrl] = useState('');
  const [notes, setNotes] = useState('');
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawMobile, setWithdrawMobile] = useState('');
  const [withdrawAccountTitle, setWithdrawAccountTitle] = useState('');
  const [isWithdrawing, setIsWithdrawing] = useState(false);
  const [sellerStats, setSellerStats] = useState({
    walletBalance: 0,
    totalEarnings: 0,
    tasksCompleted: 0,
    inProgress: 0,
    successRate: 0,
    avgCompletionTime: 0,
    rating: 1,
    ratingLabel: '1 Star',
    performanceScore: 0,
    finalReputationScore: 0,
    trustScore: 50,
    myTasks: [] as any[],
  });
  const [connectedPlatforms, setConnectedPlatforms] = useState({
    facebook: false,
    instagram: false,
    twitter: false,
    youtube: false,
  });
  const [youTubeDrawerOpen, setYouTubeDrawerOpen] = useState(false);
  const [youTubeTaskData, setYouTubeTaskData] = useState<any>(null);

  const location = useLocation();
  const navigate = useNavigate();
  const user = userData || location.state?.userData;
  const loggedInUserName = user?.userName || 'Seller';
  const userId = user?.userId;

  const fetchSellerData = async () => {
    if (!userId) return;

    try {
      const [tasksResponse, statsResponse] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/approved-tasks/?userId=${userId}`),
        fetch(`http://127.0.0.1:8000/api/seller-dashboard-stats/${userId}/`),
      ]);

      const tasksData = await tasksResponse.json();
      const statsData = await statsResponse.json();

      if (tasksResponse.ok) setAvailableTasks(tasksData.tasks || []);

      if (statsResponse.ok) {
        setSellerStats({
          walletBalance: Number(statsData.walletBalance) || 0,
          totalEarnings: Number(statsData.totalEarnings) || 0,
          tasksCompleted: Number(statsData.tasksCompleted) || 0,
          inProgress: Number(statsData.inProgress) || 0,
          successRate: Number(statsData.successRate) || 0,
          avgCompletionTime: Number(statsData.avgCompletionTime) || 0,
          rating: Number(statsData.rating) || 1,
          ratingLabel: statsData.ratingLabel || '1 Star',
          performanceScore: Number(statsData.performanceScore) || 0,
          finalReputationScore: Number(statsData.finalReputationScore) || 0,
          trustScore: Number(statsData.trustScore) || 50,
          myTasks: statsData.myTasks || [],
        });
      }
    } catch (error) {
      console.error('Seller dashboard fetch error:', error);
    }
  };

  useEffect(() => {
    fetchSellerData();
  }, [
    userId,
    connectedPlatforms.facebook,
    connectedPlatforms.instagram,
    connectedPlatforms.twitter,
    connectedPlatforms.youtube,
  ]);

  useEffect(() => {
    let interval: any;

    if (isTimerRunning) {
      interval = setInterval(() => setTimer((prev) => prev + 1), 1000);
    }

    return () => clearInterval(interval);
  }, [isTimerRunning]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getPlatformUrl = (taskOrPlatform: any) => {
    if (typeof taskOrPlatform === 'object' && taskOrPlatform?.url) return taskOrPlatform.url;
    if (activeTask?.url) return activeTask.url;

    const platform = typeof taskOrPlatform === 'object' ? taskOrPlatform?.platform : taskOrPlatform;
    const urls: any = {
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

  const handleStartTask = (task: any) => {
    if (task.platform?.toLowerCase() === 'youtube') {
      setYouTubeTaskData(task);
      setYouTubeDrawerOpen(true);
      return;
    }

    setActiveTask(task);
    setIsTaskDialogOpen(true);
    setTimer(0);
    setIsTimerRunning(true);
    setProofUrl('');
    setNotes('');

    const platformUrl = getPlatformUrl(task);
    if (platformUrl) {
      window.open(platformUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handleYouTubeComplete = async (timeSpentSeconds = 0) => {
    if (!youTubeTaskData) return;

    try {
      const response = await fetch('http://127.0.0.1:8000/api/submit-task/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          taskId: youTubeTaskData.id,
          sellerId: userId,
          proofUrl: 'watched_70_percent',
          notes: 'Auto-submitted after 70% video watch',
          timeSpent: timeSpentSeconds,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert('Task completed! YouTube watch requirement satisfied.');
        setYouTubeDrawerOpen(false);
        setYouTubeTaskData(null);
        fetchSellerData();
      } else {
        alert(data.error || 'Auto-submit failed');
      }
    } catch (error) {
      console.error('YouTube auto-submit error:', error);
    }
  };

  const handlePauseTimer = () => setIsTimerRunning(!isTimerRunning);
  const handleStopTask = () => setIsTimerRunning(false);

  const handleSubmitTask = async () => {
    if (!activeTask?.id) return;

    if (!userId) {
      alert('Please login again');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/submit-task/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          taskId: activeTask.id,
          sellerId: userId,
          proofUrl,
          notes,
          timeSpent: timer,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert(data.message || 'Task submitted successfully');
        setIsTaskDialogOpen(false);
        setActiveTask(null);
        setTimer(0);
        setIsTimerRunning(false);
        setProofUrl('');
        setNotes('');
        fetchSellerData();
      } else {
        alert(data.error || 'Submit task failed');
      }
    } catch (error) {
      console.error('Submit task error:', error);
      alert('Server error');
    }
  };

  const handleWithdrawFunds = async () => {
    if (!userId) return;

    const amount = Number(withdrawAmount);

    if (!amount || amount <= 0) {
      alert('Enter a valid amount');
      return;
    }

    if (!/^03\d{9}$/.test(withdrawMobile)) {
      alert('Enter valid EasyPaisa number like 03xxxxxxxxx');
      return;
    }

    if (!withdrawAccountTitle.trim()) {
      alert('Enter EasyPaisa account title');
      return;
    }

    setIsWithdrawing(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/withdraw-funds/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sellerId: userId,
          amount,
          easypaisaNumber: withdrawMobile,
          accountTitle: withdrawAccountTitle,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        alert(`${data.message}\nReference: ${data.withdrawalReference || 'N/A'}`);
        setWithdrawAmount('');
        setWithdrawMobile('');
        setWithdrawAccountTitle('');
        setIsWithdrawOpen(false);
        fetchSellerData();
      } else {
        alert(data.error || 'Withdraw failed');
      }
    } catch (error) {
      console.error('Withdraw error:', error);
      alert('Server error');
    } finally {
      setIsWithdrawing(false);
    }
  };

  const stats = [
    { label: 'Wallet Balance', value: `$${sellerStats.walletBalance.toFixed(2)}`, icon: DollarSign, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Tasks Completed', value: sellerStats.tasksCompleted, icon: CheckCircle, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'In Progress', value: sellerStats.inProgress, icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Rating', value: sellerStats.ratingLabel, icon: TrendingUp, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  const myTasks = sellerStats.myTasks || [];

  const getPlatformIcon = (platform: string) => {
    switch (platform?.toLowerCase()) {
      case 'instagram':
        return <Instagram className="w-5 h-5 text-pink-600" />;
      case 'youtube':
        return <Youtube className="w-5 h-5 text-red-600" />;
      case 'facebook':
        return <Facebook className="w-5 h-5 text-blue-600" />;
      case 'twitter':
        return <Twitter className="w-5 h-5 text-sky-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'assigned' || status === 'pending') return <Badge className="bg-blue-100 text-blue-700">Assigned</Badge>;
    if (status === 'completed' || status === 'approved') return <Badge className="bg-green-100 text-green-700">Completed</Badge>;
    return <Badge className="bg-red-100 text-red-700">Rejected</Badge>;
  };

  const getDifficultyBadge = (difficulty: string) => {
    if (difficulty === 'Easy') return <Badge variant="outline" className="border-green-200 text-green-700">Easy</Badge>;
    return <Badge variant="outline" className="border-orange-200 text-orange-700">Medium</Badge>;
  };

  const assignedTasks = availableTasks;
  const visibleAssignedTasks = assignedTasks;

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
              <Badge className="ml-2 bg-green-100 text-green-700">Seller</Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => { if (typeof onLogout === 'function') onLogout(); else navigate('/'); }}>
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

        <ConnectSocial
          connectedPlatforms={connectedPlatforms}
          setConnectedPlatforms={setConnectedPlatforms}
          sellerId={userId}
          theme={theme}
        />

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
                  {assignedTasks.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Zap className="w-8 h-8 text-gray-400" />
                      </div>
                      <h3 className="text-gray-900 mb-2">No Assigned Tasks</h3>
                      <p className="text-gray-500 text-sm mb-4">
                        No jobs have been assigned to you yet. Once admin approves and assigns a task, it will appear here.
                      </p>
                    </div>
                  ) : (
                    visibleAssignedTasks.map((task) => (
                      <div key={task.id} className="border border-gray-200 rounded-xl p-4 hover:border-green-200 hover:shadow-md transition-all">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {getPlatformIcon(task.platform)}
                            <div>
                              <h3 className="text-gray-900">{task.title}</h3>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-sm text-gray-500">{task.type}</span>
                                <span className="text-gray-300">-</span>
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
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="seller-earnings-card border-gray-200 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardHeader>
                <CardTitle className="text-white">Earnings Summary</CardTitle>
                <CardDescription className="text-green-100">Available for withdrawal</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-white mb-6">${sellerStats.walletBalance.toFixed(2)}</div>
                <Button className="seller-earnings-button w-full bg-white text-green-600 hover:bg-green-50 rounded-full" onClick={() => setIsWithdrawOpen(true)}>
                  Withdraw Funds
                </Button>
                <div className="mt-6 pt-6 border-t border-green-400/30 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-100">Total Earnings</span>
                    <span className="text-white">${sellerStats.totalEarnings.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-100">Completed Tasks</span>
                    <span className="text-white">{sellerStats.tasksCompleted}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-100">Pending Tasks</span>
                    <span className="text-white">{sellerStats.inProgress}</span>
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
                    <TabsTrigger value="pending" className="flex-1 text-sm">Assigned</TabsTrigger>
                    <TabsTrigger value="approved" className="flex-1 text-sm">Completed</TabsTrigger>
                  </TabsList>
                  <TabsContent value="pending" className="space-y-3">
                    {myTasks.filter((task) => task.status === 'assigned' || task.status === 'pending').map((task) => (
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
                    {myTasks.filter((task) => task.status === 'completed' || task.status === 'approved').map((task) => (
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
                <CardTitle className="text-gray-900">Seller Rating</CardTitle>
                <CardDescription>Reputation and performance score</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Current Rating</span>
                  <Badge className="bg-green-100 text-green-700">{sellerStats.ratingLabel}</Badge>
                </div>
                <Progress value={(sellerStats.rating / 5) * 100} className="h-2" />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Final Reputation</span>
                  <span className="text-gray-900">{sellerStats.finalReputationScore.toFixed(2)} / 100</span>
                </div>
                <Progress value={sellerStats.finalReputationScore} className="h-2" />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Performance Score</span>
                  <span className="text-gray-900">{sellerStats.performanceScore.toFixed(2)} / 100</span>
                </div>
                <Progress value={sellerStats.performanceScore} className="h-2" />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Trust Score</span>
                  <span className="text-gray-900">{sellerStats.trustScore.toFixed(2)} / 100</span>
                </div>
                <Progress value={sellerStats.trustScore} className="h-2" />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Success Rate</span>
                  <span className="text-green-600">{sellerStats.successRate}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg. Completion Time</span>
                  <span className="text-gray-900">{(sellerStats.avgCompletionTime * 60).toFixed(1)} min</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Dialog open={isWithdrawOpen} onOpenChange={setIsWithdrawOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Withdraw via EasyPaisa</DialogTitle>
            <DialogDescription>Send your available seller balance to your EasyPaisa account</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="rounded-xl border border-green-200 bg-green-50 p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-green-800">Available Balance</span>
                <span className="font-semibold text-green-900">${sellerStats.walletBalance.toFixed(2)}</span>
              </div>
            </div>
            <div>
              <Label htmlFor="withdraw-mobile">EasyPaisa Number</Label>
              <Input
                id="withdraw-mobile"
                inputMode="numeric"
                maxLength={11}
                placeholder="03xxxxxxxxx"
                value={withdrawMobile}
                onChange={(event) => setWithdrawMobile(event.target.value.replace(/\D/g, '').slice(0, 11))}
              />
            </div>
            <div>
              <Label htmlFor="withdraw-title">Account Title</Label>
              <Input
                id="withdraw-title"
                placeholder="Account holder name"
                value={withdrawAccountTitle}
                onChange={(event) => setWithdrawAccountTitle(event.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="withdraw-amount">Amount</Label>
              <Input
                id="withdraw-amount"
                type="number"
                min="1"
                step="0.01"
                placeholder="500"
                value={withdrawAmount}
                onChange={(event) => setWithdrawAmount(event.target.value)}
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button
                className="flex-1 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full"
                onClick={handleWithdrawFunds}
                disabled={isWithdrawing}
              >
                {isWithdrawing ? 'Submitting...' : 'Submit Request'}
              </Button>
              <Button variant="outline" className="flex-1 rounded-full" onClick={() => setIsWithdrawOpen(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

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
                      <span className="text-gray-300">-</span>
                      <span className="text-sm text-green-600 font-medium">${activeTask.price} per task</span>
                    </div>
                  </div>
                </div>
                {getDifficultyBadge(activeTask.difficulty)}
              </div>

              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-xl">
                <div className="flex items-center gap-3">
                  <Button size="sm" variant="outline" onClick={handlePauseTimer} className="rounded-full">
                    {isTimerRunning ? <><Pause className="w-4 h-4 mr-1" /> Pause</> : <><Play className="w-4 h-4 mr-1" /> Resume</>}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleStopTask} className="rounded-full text-red-600 border-red-200 hover:bg-red-50">
                    <StopCircle className="w-4 h-4 mr-1" /> Stop
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-green-600" />
                  <span className="text-2xl font-mono font-bold text-gray-900">{formatTime(timer)}</span>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Instructions:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>- The task has been opened in a new browser tab.</li>
                  <li>- Complete the {activeTask.type} action on that tab.</li>
                  <li>- Take a screenshot or copy the URL as proof.</li>
                  <li>- Paste the proof URL below and submit the task.</li>
                </ul>
              </div>

              <div className="space-y-4 pt-2">
                <div className="space-y-2">
                  <Label htmlFor="proofUrl" className="text-sm font-medium">Proof URL / Screenshot Link *</Label>
                  <Input id="proofUrl" value={proofUrl} onChange={(event) => setProofUrl(event.target.value)} placeholder="https://imgur.com/screenshot or profile URL" className="border-gray-300" />
                  <p className="text-xs text-gray-500">Provide a link to your screenshot or the profile/post URL</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes" className="text-sm font-medium">Additional Notes (Optional)</Label>
                  <Textarea id="notes" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Add any relevant information..." rows={3} className="border-gray-300" />
                </div>
              </div>

              <div className="flex gap-3 pt-4 border-t">
                <Button className="flex-1 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full" onClick={handleSubmitTask} disabled={!proofUrl}>
                  <Upload className="w-4 h-4 mr-2" /> Submit Task
                </Button>
                <Button variant="outline" className="rounded-full" onClick={() => setIsTaskDialogOpen(false)}>Cancel</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {youTubeDrawerOpen && youTubeTaskData && (
        <YouTubeDrawer
          videoUrl={youTubeTaskData.url}
          onClose={() => {
            setYouTubeDrawerOpen(false);
            setYouTubeTaskData(null);
          }}
          onComplete={handleYouTubeComplete}
        />
      )}
    </div>
  );
}

const styles = {
  backdrop: {
    position: 'fixed' as const,
    inset: 0,
    background: 'rgba(0,0,0,0.5)',
    zIndex: 1000,
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'center',
  },
  drawer: {
    width: '100%',
    background: '#fff',
    borderRadius: '20px 20px 0 0',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    boxShadow: '0 -4px 20px rgba(0,0,0,0.1)',
  },
  handle: {
    width: 40,
    height: 4,
    background: '#ddd',
    borderRadius: 2,
    margin: '12px auto 0',
    flexShrink: 0,
  },
  drawerHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 20px',
    borderBottom: '1px solid #f0f0f0',
    flexShrink: 0,
  },
  platformBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  platformIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f2f2f2',
  },
  platformName: {
    fontSize: 15,
    fontWeight: 600,
    color: '#111',
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: '50%',
    border: 'none',
    background: '#f2f2f2',
    cursor: 'pointer',
    fontSize: 14,
    color: '#555',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  drawerBody: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '16px',
  },
};
