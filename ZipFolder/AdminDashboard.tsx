import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Users, DollarSign, AlertTriangle, TrendingUp, CheckCircle, XCircle, Eye, Ban, LogOut, Zap, Search, Star, ChevronLeft, ChevronRight, ShieldCheck } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import AssignedSellersModal from './AssignedSellersModal';

const API_BASE_URL = 'https://caddie-unlearned-author.ngrok-free.dev';
const FRAUD_STATS_API_URL = `${API_BASE_URL}/api/fraud-stats/`;

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
  const [adminSection, setAdminSection] = useState('home');
  const [approvingTaskIds, setApprovingTaskIds] = useState([]);
  const [assignedSellersDialogOpen, setAssignedSellersDialogOpen] = useState(false);
  const [assignedSellersData, setAssignedSellersData] = useState({ task: null, sellers: [] });
  const [isAssignedSellersLoading, setIsAssignedSellersLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(emptyDashboardData);
  const [sellerMonitor, setSellerMonitor] = useState({
    onlineSellers: [],
    sellers: [],
    proofs: [],
  });
  const [fraudDetectionResults, setFraudDetectionResults] = useState([]);
  const [isFraudDataLoading, setIsFraudDataLoading] = useState(false);
  const [openedFraudProofId, setOpenedFraudProofId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const assignedSellerModalSellers = assignedSellersData.sellers.map((seller) => ({
    id: seller.sellerId || seller.jobId,
    name: seller.name,
    email: seller.email,
    trust_score: Number(seller.trustScore) || 0,
    reputation_score: Number(seller.finalReputationScore) || 0,
    proof_status: seller.proofStatus,
    audit_status: seller.auditStatus,
    rating: Number(seller.rating) || 1,
    rating_label: seller.ratingLabel || `${seller.rating || 1} Star`,
    submission_status: seller.jobStatus,
  }));

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

  const fetchSellerMonitor = async () => {
    const response = await fetch(`${API_BASE_URL}/api/admin-seller-monitor/`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Seller monitor fetch failed');
    }

    setSellerMonitor({
      onlineSellers: data.onlineSellers || [],
      sellers: data.sellers || [],
      proofs: data.proofs || [],
    });
  };

  const fetchFraudDetectionResults = async () => {
    setIsFraudDataLoading(true);

    try {
      const response = await fetch(FRAUD_STATS_API_URL);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Fraud stats fetch failed');
      }

      setFraudDetectionResults(data.results || []);
    } catch (error) {
      console.error('Fraud detection fetch error:', error);
      setFraudDetectionResults([]);
    } finally {
      setIsFraudDataLoading(false);
    }
  };

  const refreshAdminData = async ({ showLoader = true, showAlert = true } = {}) => {
    if (showLoader) {
      setIsLoading(true);
    }

    try {
      await Promise.all([fetchAdminSummary(), fetchPendingTasks(), fetchActiveTasks(), fetchSellerMonitor(), fetchFraudDetectionResults()]);
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

  const fetchJobs = async (sellersObj, goal) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ml/allocate-jobs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ total_jobs: goal, sellers: sellersObj }),
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
    if (approvingTaskIds.includes(taskId)) return;
    setApprovingTaskIds((prev) => [...prev, taskId]);

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
      const goal = data.goal || 0;
      console.log(goal)
      const sellersObj = await fetchSellers();
      const allocation = await fetchJobs(sellersObj,goal);
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

  const handleViewAssignedSellers = async (taskId) => {
    setAssignedSellersDialogOpen(true);
    setIsAssignedSellersLoading(true);
    setAssignedSellersData({ task: null, sellers: [] });

    try {
      const response = await fetch(`${API_BASE_URL}/api/admin-active-tasks/${taskId}/assigned-sellers/`);
      const data = await response.json();

      if (response.ok) {
        setAssignedSellersData({
          task: data.task || null,
          sellers: data.sellers || [],
        });
      } else {
        alert(data.error || 'Could not load assigned sellers');
        setAssignedSellersDialogOpen(false);
      }
    } catch (error) {
      console.error('Assigned sellers fetch error:', error);
      alert('Server error');
      setAssignedSellersDialogOpen(false);
    } finally {
      setIsAssignedSellersLoading(false);
    }
  };

  const handleProofReview = async (jobId, proofStatus) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/seller-proof/${jobId}/review/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proofStatus }),
      });
      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        refreshAdminData({ showLoader: false });
      } else {
        alert(data.error || 'Proof review failed');
      }
    } catch (error) {
      console.error(error);
      alert('Server error');
    } finally {
      setApprovingTaskIds((prev) => prev.filter((id) => id !== jobId));
    }
  };

  const handleAuditReview = async (jobId, auditStatus) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/seller-audit/${jobId}/review/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auditStatus }),
      });
      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        refreshAdminData({ showLoader: false });
      } else {
        alert(data.error || 'Audit review failed');
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

  const getRatingBadge = (rating) => {
    if (rating >= 5) return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">5 Star</Badge>;
    if (rating >= 4) return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">4 Star</Badge>;
    if (rating >= 3) return <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">3 Star</Badge>;
    if (rating >= 2) return <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">2 Star</Badge>;
    return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">1 Star</Badge>;
  };

  const getRiskBadge = (probability) => {
    if (probability >= 70) return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">{probability}% High Risk</Badge>;
    if (probability >= 40) return <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">{probability}% Medium Risk</Badge>;
    return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">{probability}% Low Risk</Badge>;
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

  const SellerTable = ({ sellers, emptyMessage }) => {
    const [sellerSearch, setSellerSearch] = useState('');
    const [sellerStatusFilter, setSellerStatusFilter] = useState('all');
    const [sellerRatingFilter, setSellerRatingFilter] = useState('all');
    const [sellerPage, setSellerPage] = useState(1);
    const sellersPerPage = 5;

    const getInitials = (name = '') => {
      const parts = name.trim().split(/\s+/).filter(Boolean);
      if (!parts.length) return 'S';
      return parts.slice(0, 2).map((part) => part[0]?.toUpperCase()).join('');
    };

    const getTrustColor = (score) => {
      if (score >= 70) return 'bg-green-500';
      if (score >= 40) return 'bg-amber-500';
      return 'bg-red-500';
    };

    const getReputationColor = (score) => {
      if (score >= 70) return 'bg-green-500';
      if (score >= 40) return 'bg-amber-500';
      return 'bg-red-500';
    };

    const getSellerRatingBadge = (rating) => {
      if (rating >= 5) return 'bg-green-100 text-green-700 border-green-200';
      if (rating >= 4) return 'bg-blue-100 text-blue-700 border-blue-200';
      if (rating >= 3) return 'bg-amber-100 text-amber-700 border-amber-200';
      if (rating >= 2) return 'bg-orange-100 text-orange-700 border-orange-200';
      return 'bg-red-100 text-red-700 border-red-200';
    };

    const filteredSellers = sellers.filter((seller) => {
      const query = sellerSearch.toLowerCase().trim();
      const matchesSearch = !query
        || seller.name?.toLowerCase().includes(query)
        || seller.email?.toLowerCase().includes(query);
      const matchesStatus = sellerStatusFilter === 'all'
        || (sellerStatusFilter === 'online' && seller.isOnline)
        || (sellerStatusFilter === 'offline' && !seller.isOnline);
      const matchesRating = sellerRatingFilter === 'all'
        || Number(seller.rating) === Number(sellerRatingFilter);

      return matchesSearch && matchesStatus && matchesRating;
    });

    const totalPages = Math.max(1, Math.ceil(filteredSellers.length / sellersPerPage));
    const currentPage = Math.min(sellerPage, totalPages);
    const pageStart = (currentPage - 1) * sellersPerPage;
    const visibleSellers = filteredSellers.slice(pageStart, pageStart + sellersPerPage);

    const handleSearchChange = (value) => {
      setSellerSearch(value);
      setSellerPage(1);
    };

    const handleStatusFilterChange = (value) => {
      setSellerStatusFilter(value);
      setSellerPage(1);
    };

    const handleRatingFilterChange = (value) => {
      setSellerRatingFilter(value);
      setSellerPage(1);
    };

    return (
      <div className="seller-management-table overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b border-gray-100 bg-gradient-to-r from-white to-gray-50 p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="shrink-0">
            <h3 className="text-base font-semibold text-gray-900">Seller Management</h3>
            <p className="text-xs text-gray-500">Search, filter, and monitor seller reputation.</p>
          </div>
          <div
            className="flex flex-col gap-2 sm:flex-row sm:items-center"
            style={{ width: '100%', maxWidth: 620 }}
          >
            <div className="relative min-w-0 flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                value={sellerSearch}
                onChange={(event) => handleSearchChange(event.target.value)}
                placeholder="Search seller..."
                className="h-9 w-full rounded-full border border-gray-200 bg-white pl-10 pr-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-green-400 focus:ring-2 focus:ring-green-100"
              />
            </div>
            <select
              value={sellerStatusFilter}
              onChange={(event) => handleStatusFilterChange(event.target.value)}
              className="h-9 rounded-full border border-gray-200 bg-white px-3 text-sm text-gray-700 outline-none transition focus:border-green-400 focus:ring-2 focus:ring-green-100 sm:w-[150px]"
            >
              <option value="all">All Status</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
            </select>
            <select
              value={sellerRatingFilter}
              onChange={(event) => handleRatingFilterChange(event.target.value)}
              className="h-9 rounded-full border border-gray-200 bg-white px-3 text-sm text-gray-700 outline-none transition focus:border-green-400 focus:ring-2 focus:ring-green-100 sm:w-[150px]"
            >
              <option value="all">All Ratings</option>
              <option value="5">5 Star</option>
              <option value="4">4 Star</option>
              <option value="3">3 Star</option>
              <option value="2">2 Star</option>
              <option value="1">1 Star</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] table-fixed border-collapse">
            <colgroup>
              <col style={{ width: '28%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '17%' }} />
              <col style={{ width: '14%' }} />
              <col style={{ width: '13%' }} />
              <col style={{ width: '15%' }} />
            </colgroup>
            <thead className="sticky top-0 z-10 bg-gray-50/95 backdrop-blur">
              <tr className="border-b border-gray-200 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                <th className="px-5 py-3 text-left align-middle" style={{ paddingLeft: 76 }}>Seller</th>
                <th className="px-5 py-3 text-left align-middle">Status</th>
                <th className="px-5 py-3 text-left align-middle">Trust</th>
                <th className="px-5 py-3 text-left align-middle">Rating</th>
                <th className="px-5 py-3 text-left align-middle">Reputation</th>
                <th className="px-5 py-3 text-left align-middle">Proofs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {!visibleSellers.length ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-gray-500">
                    {sellers.length ? 'No sellers match your filters.' : emptyMessage}
                  </td>
                </tr>
              ) : (
                visibleSellers.map((seller) => {
                  const trustScore = Number(seller.trustScore) || 0;
                  const reputationScore = Number(seller.finalReputationScore) || 0;

                  return (
                    <tr key={seller.id} className="h-[76px] transition hover:bg-green-50/40">
                      <td className="px-5 py-4 align-middle">
                          <div className="flex items-center gap-3">
                          <div
                            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold shadow-sm"
                            style={{
                              background: 'linear-gradient(135deg, #0f172a 0%, #0f766e 100%)',
                              color: '#ffffff',
                              borderRadius: '9999px',
                            }}
                          >
                            {getInitials(seller.name)}
                          </div>
                          <div className="min-w-0">
                            <div className="truncate text-sm font-semibold text-gray-900">{seller.name}</div>
                            <div className="truncate text-xs text-gray-500">{seller.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-middle">
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${seller.isOnline ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                          <span className={`h-2 w-2 rounded-full ${seller.isOnline ? 'bg-green-500' : 'bg-gray-400'}`} />
                          {seller.isOnline ? 'Online' : 'Offline'}
                        </span>
                      </td>
                      <td className="px-5 py-4 align-middle">
                        <div className="w-[130px]">
                          <div className="mb-1 flex items-center gap-2 text-xs">
                            <span className="flex items-center gap-1 text-gray-500"><ShieldCheck className="h-3.5 w-3.5" /> Trust</span>
                            <span className="font-semibold text-gray-900">{trustScore.toFixed(2)}</span>
                          </div>
                          <div className="h-2 rounded-full bg-gray-100">
                            <div className={`h-2 rounded-full ${getTrustColor(trustScore)}`} style={{ width: `${Math.max(0, Math.min(100, trustScore))}%` }} />
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-middle">
                        <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${getSellerRatingBadge(Number(seller.rating))}`}>
                          <Star className="h-3.5 w-3.5 fill-current" />
                          {seller.rating} Star
                        </span>
                      </td>
                      <td className="px-5 py-4 align-middle">
                        <div className="flex items-center gap-2">
                          <span className={`h-2.5 w-2.5 rounded-full ${getReputationColor(reputationScore)}`} />
                          <span className="text-sm font-semibold text-gray-900">{reputationScore.toFixed(2)}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 align-middle">
                        <div className="whitespace-nowrap text-sm font-medium">
                          <span className="text-green-600">{seller.validProofs} valid</span>
                          <span className="mx-1 text-gray-300">/</span>
                          <span className="text-red-600">{seller.invalidProofs} invalid</span>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col gap-3 border-t border-gray-100 bg-gray-50/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-gray-500">
            Showing {visibleSellers.length ? pageStart + 1 : 0}-{Math.min(pageStart + sellersPerPage, filteredSellers.length)} of {filteredSellers.length} sellers
          </p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="h-8 rounded-full"
              onClick={() => setSellerPage((page) => Math.max(1, page - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-gray-700 shadow-sm">
              Page {currentPage} / {totalPages}
            </span>
            <Button
              size="sm"
              variant="outline"
              className="h-8 rounded-full"
              onClick={() => setSellerPage((page) => Math.min(totalPages, page + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  };

  const normalizeId = (value) => {
    if (value === null || value === undefined || value === '') return '';
    return String(value);
  };

  const safeDisplay = (value, fallback = 'N/A') => {
    if (value === null || value === undefined || value === '') return fallback;
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'object') return JSON.stringify(value);
    return value;
  };

  const getFraudMatchForProof = (proof) => {
    return fraudDetectionResults.find((result) => {
      const proofJobId = normalizeId(proof.jobId || proof.job_id || proof.currentJobId || proof.current_job_id);
      const resultJobId = normalizeId(result.job_id || result.current_job_id || result.current_job?.id || result.job?.id || result.job);

      const proofTaskId = normalizeId(proof.taskId || proof.task_id || proof.task?.id);
      const resultTaskId = normalizeId(result.task_id || result.task?.id);

      const proofSellerId = normalizeId(proof.sellerId || proof.seller_id || proof.seller?.id || proof.userId || proof.user_id);
      const resultSellerId = normalizeId(result.seller_id || result.seller?.id || result.user_id);

      const proofFraudId = normalizeId(proof.fraudId || proof.fraud_id);
      const resultFraudId = normalizeId(result.id);

      if (proofFraudId && resultFraudId && proofFraudId === resultFraudId) return true;
      if (proofJobId && resultJobId && proofJobId === resultJobId) return true;
      if (proofTaskId && resultTaskId && proofTaskId === resultTaskId && (!proofSellerId || !resultSellerId || proofSellerId === resultSellerId)) return true;

      const sameTitle = String(proof.taskTitle || '').trim().toLowerCase() === String(result.task_title || '').trim().toLowerCase();
      const sameSeller = String(proof.sellerName || '').trim().toLowerCase() === String(result.seller_name || '').trim().toLowerCase();

      return sameTitle && sameSeller;
    });
  };

  const getProofFraudData = (proof) => {
    const matchedFraud = getFraudMatchForProof(proof);
    const probability = Number(
      matchedFraud?.fraud_probability
      ?? proof.fraudProbability
      ?? proof.fraud_probability
      ?? 0
    );
    const riskLevel = matchedFraud?.risk_level || proof.riskLevel || proof.risk_level || getRiskLevelFromProbability(probability);
    const suspiciousSignals = Array.isArray(matchedFraud?.suspicious_signals)
      ? matchedFraud.suspicious_signals
      : Array.isArray(proof.suspiciousSignals)
        ? proof.suspiciousSignals
        : Array.isArray(proof.suspicious_signals)
          ? proof.suspicious_signals
          : [];
    const fraudReasons = matchedFraud?.fraud_reasons ?? proof.fraudReasons ?? proof.fraud_reasons ?? proof.fraudCauses ?? [];
    const prediction = matchedFraud?.prediction || proof.prediction || (probability >= 50 ? 'FRAUD' : 'LEGITIMATE');
    const isFraud = matchedFraud?.is_fraud ?? proof.isFraud ?? proof.is_fraud ?? probability >= 50;

    return {
      ...matchedFraud,
      probability,
      riskLevel,
      suspiciousSignals,
      fraudReasons,
      prediction,
      isFraud,
    };
  };

  const getRiskLevelFromProbability = (probability) => {
    if (probability >= 80) return 'CRITICAL';
    if (probability >= 70) return 'HIGH';
    if (probability >= 40) return 'MEDIUM';
    return 'LOW';
  };

  const getRiskBadgeFromFraud = (probability, riskLevel) => {
    const normalizedRisk = riskLevel || getRiskLevelFromProbability(probability);

    if (normalizedRisk === 'CRITICAL' || probability >= 80) {
      return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">{probability}% Critical Risk</Badge>;
    }
    if (normalizedRisk === 'HIGH' || probability >= 70) {
      return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">{probability}% High Risk</Badge>;
    }
    if (normalizedRisk === 'MEDIUM' || probability >= 40) {
      return <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">{probability}% Medium Risk</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">{probability}% Low Risk</Badge>;
  };

  const getFraudBarColor = (probability, riskLevel) => {
    if (riskLevel === 'CRITICAL' || probability >= 80) return 'bg-red-600';
    if (riskLevel === 'HIGH' || probability >= 70) return 'bg-red-500';
    if (riskLevel === 'MEDIUM' || probability >= 40) return 'bg-orange-500';
    return 'bg-green-500';
  };

  const renderFraudReasonItems = (reasons) => {
    if (!reasons || reasons.length === 0) {
      return <Badge variant="outline" className="text-xs">No strong fraud signals</Badge>;
    }

    if (typeof reasons === 'string') {
      return <Badge variant="outline" className="text-xs">{reasons}</Badge>;
    }

    if (Array.isArray(reasons)) {
      return reasons.slice(0, 4).map((reason, index) => {
        const label = typeof reason === 'object'
          ? reason.reason || reason.feature || 'Fraud reason'
          : String(reason);

        return <Badge key={`${label}-${index}`} variant="outline" className="text-xs">{label}</Badge>;
      });
    }

    if (typeof reasons === 'object') {
      return <Badge variant="outline" className="text-xs">{reasons.reason || reasons.feature || 'Fraud reason found'}</Badge>;
    }

    return <Badge variant="outline" className="text-xs">{String(reasons)}</Badge>;
  };

  const FraudReasonsBlock = ({ reasons }) => {
    if (!reasons || reasons.length === 0) {
      return <p className="text-xs text-gray-500">No fraud reason found.</p>;
    }

    if (typeof reasons === 'string') {
      return <p className="rounded-xl border border-orange-100 bg-white p-3 text-sm text-orange-900">{reasons}</p>;
    }

    if (Array.isArray(reasons)) {
      return (
        <div className="space-y-2">
          {reasons.map((reason, index) => {
            if (typeof reason === 'object') {
              return (
                <div key={index} className="rounded-xl border border-orange-100 bg-white p-3 text-sm text-orange-900">
                  <p className="font-semibold">{reason.reason || reason.feature || 'Fraud reason'}</p>
                  {reason.layer && <p className="mt-1 text-xs text-orange-700">Layer: {reason.layer}</p>}
                  {reason.impact !== undefined && <p className="mt-1 text-xs text-orange-700">Impact: {reason.impact}</p>}
                </div>
              );
            }

            return <div key={index} className="rounded-xl border border-orange-100 bg-white p-3 text-sm text-orange-900">{String(reason)}</div>;
          })}
        </div>
      );
    }

    if (typeof reasons === 'object') {
      return <pre className="overflow-x-auto rounded-xl bg-gray-900 p-3 text-xs text-green-100">{JSON.stringify(reasons, null, 2)}</pre>;
    }

    return <p className="rounded-xl border border-orange-100 bg-white p-3 text-sm text-orange-900">{String(reasons)}</p>;
  };

  const ProofReviewList = ({ proofs }) => {
    // Only show proof submissions that still need proof approval.
    // After Accept/Reject, backend already releases the seller back to the queue,
    // so keeping accepted proofs visible here made the same job look duplicated/stuck.
    const pendingReviewProofs = proofs.filter((proof) => proof.proofStatus === 'pending');

    const normalizeProbability = (value) => {
      const numericValue = Number(value || 0);
      const percentageValue = numericValue > 0 && numericValue <= 1 ? numericValue * 100 : numericValue;
      return Math.max(0, Math.min(100, Number(percentageValue.toFixed(1))));
    };

    const getFraudBarStyle = (probability, riskLevel) => {
      let background = 'linear-gradient(90deg, #16a34a, #22c55e)';

      if (riskLevel === 'CRITICAL' || probability >= 80) {
        background = 'linear-gradient(90deg, #ef4444, #b91c1c)';
      } else if (riskLevel === 'HIGH' || probability >= 70) {
        background = 'linear-gradient(90deg, #f97316, #dc2626)';
      } else if (riskLevel === 'MEDIUM' || probability >= 40) {
        background = 'linear-gradient(90deg, #f59e0b, #f97316)';
      }

      return {
        width: `${probability}%`,
        minWidth: probability > 0 ? '8px' : '0px',
        background,
      };
    };

    const getFraudDotClass = (probability, riskLevel) => {
      if (riskLevel === 'CRITICAL' || probability >= 80) return 'bg-red-600';
      if (riskLevel === 'HIGH' || probability >= 70) return 'bg-red-500';
      if (riskLevel === 'MEDIUM' || probability >= 40) return 'bg-orange-500';
      return 'bg-green-500';
    };

    if (!pendingReviewProofs.length) {
      return <div className="text-center py-10 text-sm text-gray-500">No submitted proofs yet.</div>;
    }

    return (
      <div className="space-y-4">
        {isFraudDataLoading && (
          <div className="rounded-2xl border border-green-100 bg-green-50 px-4 py-3 text-sm text-green-700">
            Loading latest fraud detection results...
          </div>
        )}

        {pendingReviewProofs.map((proof) => {
          const isProofReviewed = proof.proofStatus === 'valid' || proof.proofStatus === 'invalid';
          const isAuditReviewed = proof.auditStatus === 'passed' || proof.auditStatus === 'failed';
          const proofMediaUrl = proof.proofImageUrl || proof.proofUrl;
          const fraudData = getProofFraudData(proof);
          const fraudProbability = normalizeProbability(fraudData.probability);
          const riskLevel = fraudData.riskLevel || getRiskLevelFromProbability(fraudProbability);
          const suspiciousSignals = Array.isArray(fraudData.suspiciousSignals) ? fraudData.suspiciousSignals : [];
          const fraudReasons = fraudData.fraudReasons;
          const isOpen = openedFraudProofId === proof.jobId;
          const topSignal = suspiciousSignals[0];

          return (
            <div key={proof.jobId} className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-green-200 hover:shadow-md">
              <div className="flex flex-col gap-4 p-4 lg:flex-row">
                <div className="w-full flex-shrink-0 lg:w-52">
                  <div className="aspect-video overflow-hidden rounded-xl border border-gray-200 bg-gray-100 flex items-center justify-center">
                    {proofMediaUrl ? (
                      <img src={proofMediaUrl} alt="Submitted proof" className="h-full w-full object-cover transition duration-300 hover:scale-105" />
                    ) : (
                      <span className="text-xs text-gray-500">No proof image</span>
                    )}
                  </div>
                  {proofMediaUrl && (
                    <Button size="sm" variant="outline" className="mt-2 w-full rounded-full text-xs" onClick={() => window.open(proofMediaUrl, '_blank', 'noopener,noreferrer')}>
                      <Eye className="mr-2 h-4 w-4" />
                      Open Proof
                    </Button>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <h3 className="truncate text-sm font-semibold text-gray-900 sm:text-base">{proof.taskTitle}</h3>
                        <span className={`h-2.5 w-2.5 rounded-full ${getFraudDotClass(fraudProbability, riskLevel)}`} />
                      </div>
                      <p className="text-xs text-gray-500 sm:text-sm">{proof.sellerName} - {proof.platform} {proof.taskType}</p>
                    </div>
                    <div className="flex flex-wrap gap-2 sm:justify-end">
                      {getRatingBadge(proof.rating)}
                      {getRiskBadgeFromFraud(fraudProbability, riskLevel)}
                    </div>
                  </div>

                  <div className="mb-3 grid gap-2 text-xs sm:grid-cols-2 sm:text-sm">
                    <div className="text-gray-600">Trust Score: <span className="font-medium text-gray-900">{Number(proof.trustScore || 0).toFixed(2)}</span></div>
                    <div className="text-gray-600">Submitted: <span className="font-medium text-gray-900">{proof.submittedAt || fraudData.analyzed_at || 'N/A'}</span></div>
                    <div className="text-gray-600">Proof Status: <span className="font-medium text-gray-900">{proof.proofStatus}</span></div>
                    <div className="text-gray-600">Audit Status: <span className="font-medium text-gray-900">{proof.auditStatus}</span></div>
                  </div>

                  <div className="mb-3 rounded-2xl border border-gray-100 bg-gradient-to-r from-gray-50 to-white p-3">
                    <div className="mb-2 flex items-center justify-between gap-2 text-xs">
                      <div>
                        <p className="font-semibold text-gray-900">AI Fraud Probability</p>
                        <p className="text-gray-500">{safeDisplay(fraudData.prediction)} · {suspiciousSignals.length} signal{suspiciousSignals.length === 1 ? '' : 's'}</p>
                      </div>
                      <span className="rounded-full bg-white px-2.5 py-1 font-bold text-gray-900 shadow-sm">{fraudProbability}%</span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200 shadow-inner">
                      <div
                        className="h-full rounded-full transition-all duration-500 ease-out"
                        style={getFraudBarStyle(fraudProbability, riskLevel)}
                      />
                    </div>
                  </div>

                  <div className="mb-3 flex flex-wrap gap-2">
                    {topSignal ? (
                      <Badge variant="outline" className="max-w-full border-orange-200 bg-orange-50 text-xs text-orange-700">
                        {topSignal.reason || topSignal.feature || 'Suspicious signal found'}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-green-200 bg-green-50 text-xs text-green-700">No strong fraud signals</Badge>
                    )}
                    {suspiciousSignals.length > 1 && (
                      <Badge variant="outline" className="text-xs">+{suspiciousSignals.length - 1} more</Badge>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {!isProofReviewed && (
                      <>
                        <Button size="sm" className="rounded-full bg-green-600 text-white hover:bg-green-700" onClick={() => handleProofReview(proof.jobId, 'valid')}>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Valid Proof
                        </Button>
                        <Button size="sm" variant="destructive" className="rounded-full" onClick={() => handleProofReview(proof.jobId, 'invalid')}>
                          <XCircle className="mr-2 h-4 w-4" />
                          Invalid Proof
                        </Button>
                      </>
                    )}
                    {!isAuditReviewed && (
                      <>
                        <Button size="sm" variant="outline" className="rounded-full" onClick={() => handleAuditReview(proof.jobId, 'passed')}>
                          Audit Passed
                        </Button>
                        <Button size="sm" variant="outline" className="rounded-full border-red-200 text-red-600 hover:bg-red-50" onClick={() => handleAuditReview(proof.jobId, 'failed')}>
                          Audit Failed
                        </Button>
                      </>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="rounded-full border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                      onClick={() => setOpenedFraudProofId(isOpen ? null : proof.jobId)}
                    >
                      {isOpen ? 'Hide Details' : 'More'}
                    </Button>
                  </div>
                </div>
              </div>

              {isOpen && (
                <div className="border-t border-gray-100 bg-gray-50/70 p-4">
                  <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-xl border border-gray-200 bg-white p-3">
                      <p className="text-xs text-gray-500">Fraud ID</p>
                      <p className="mt-1 text-sm font-semibold text-gray-900">{safeDisplay(fraudData.id, 'Not linked')}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-white p-3">
                      <p className="text-xs text-gray-500">Risk Level</p>
                      <p className="mt-1 text-sm font-semibold text-gray-900">{safeDisplay(riskLevel)}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-white p-3">
                      <p className="text-xs text-gray-500">Duplicate Screenshot</p>
                      <p className="mt-1 text-sm font-semibold text-gray-900">{safeDisplay(fraudData.is_duplicate_screenshot)}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-white p-3">
                      <p className="text-xs text-gray-500">Timing Risk</p>
                      <p className="mt-1 text-sm font-semibold text-gray-900">{safeDisplay(fraudData.timing_risk_score)}</p>
                    </div>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-[1.35fr_0.9fr]">
                    <div className="rounded-2xl border border-gray-200 bg-white p-4">
                      <div className="mb-3 flex items-center justify-between gap-2">
                        <div>
                          <h4 className="text-sm font-semibold text-gray-900">Suspicious Signals</h4>
                          <p className="text-xs text-gray-500">Detailed layer-wise evidence from fraud detection.</p>
                        </div>
                        <Badge className="bg-green-100 text-green-700 hover:bg-green-100">{suspiciousSignals.length} signals</Badge>
                      </div>

                      {!suspiciousSignals.length ? (
                        <p className="text-sm text-gray-500">No suspicious signal found.</p>
                      ) : (
                        <div className="space-y-2">
                          {suspiciousSignals.map((signal, index) => (
                            <div key={index} className="rounded-xl border border-orange-100 bg-orange-50/60 p-3">
                              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                  <p className="text-sm font-semibold text-gray-900">{signal.reason || 'Suspicious activity detected'}</p>
                                  <p className="mt-1 text-xs text-gray-500">{signal.layer || 'Unknown layer'}</p>
                                </div>
                                <Badge className="w-fit bg-red-100 text-xs text-red-700 hover:bg-red-100">Impact: {safeDisplay(signal.impact)}</Badge>
                              </div>
                              <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                                <div className="rounded-lg bg-white p-2">
                                  <p className="text-gray-500">Feature</p>
                                  <p className="mt-1 truncate font-semibold text-gray-900">{safeDisplay(signal.feature)}</p>
                                </div>
                                <div className="rounded-lg bg-white p-2">
                                  <p className="text-gray-500">Value</p>
                                  <p className="mt-1 font-semibold text-gray-900">{safeDisplay(signal.value)}</p>
                                </div>
                                <div className="rounded-lg bg-white p-2">
                                  <p className="text-gray-500">Impact</p>
                                  <p className="mt-1 font-semibold text-gray-900">{safeDisplay(signal.impact)}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="rounded-2xl border border-orange-100 bg-orange-50 p-4">
                      <h4 className="mb-2 text-sm font-semibold text-orange-900">Fraud Reasons</h4>
                      <FraudReasonsBlock reasons={fraudReasons} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
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
              onClick={() => {
                if (stat.view) {
                  setTaskView(stat.view);
                  setAdminSection('tasks');
                }
              }}
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

        <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
          {[
            { key: 'home', label: 'Home Sellers' },
            { key: 'tasks', label: 'Tasks' },
            { key: 'proofs', label: 'Proofs & Fraud' },
          ].map((section) => (
            <Button
              key={section.key}
              variant={adminSection === section.key ? 'default' : 'outline'}
              className={`rounded-full whitespace-nowrap ${adminSection === section.key ? 'bg-green-600 hover:bg-green-700 text-white' : ''}`}
              onClick={() => setAdminSection(section.key)}
            >
              {section.label}
            </Button>
          ))}
        </div>

        {adminSection === 'home' && (
          <Card className="border-gray-200 rounded-2xl mb-6 sm:mb-8">
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-gray-900 text-base sm:text-lg">Online Sellers</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Active sellers with trust score and reputation rating</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              <SellerTable sellers={sellerMonitor.onlineSellers} emptyMessage="No online sellers found." />
            </CardContent>
          </Card>
        )}

        {adminSection === 'tasks' && (
          <>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8 mb-6 sm:mb-8">
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
                  <div className="flex items-center gap-2 flex-wrap">
                    <Button
                      size="sm"
                      variant={taskView === 'pending' ? 'default' : 'outline'}
                      className={`rounded-full text-xs h-8 ${taskView === 'pending' ? 'bg-green-600 hover:bg-green-700 text-white' : ''}`}
                      onClick={() => setTaskView('pending')}
                    >
                      Pending Tasks
                    </Button>
                    <Button
                      size="sm"
                      variant={taskView === 'active' ? 'default' : 'outline'}
                      className={`rounded-full text-xs h-8 ${taskView === 'active' ? 'bg-green-600 hover:bg-green-700 text-white' : ''}`}
                      onClick={() => setTaskView('active')}
                    >
                      Active Tasks
                    </Button>
                    <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100 w-fit text-xs sm:text-sm">
                      {visibleTasks.length} {taskView === 'active' ? 'Active' : 'Pending'}
                    </Badge>
                  </div>
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
                              <Button
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 text-white rounded-full text-xs h-8"
                                onClick={() => handleApprove(task.id)}
                                disabled={approvingTaskIds.includes(task.id)}
                              >
                                <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                                <span className="hidden sm:inline">{approvingTaskIds.includes(task.id) ? 'Approving...' : 'Approve'}</span>
                              </Button>
                              <Button size="sm" variant="destructive" className="rounded-full text-xs h-8" onClick={() => handleReject(task.id)}>
                                <XCircle className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
                                <span className="hidden sm:inline">Reject</span>
                              </Button>
                            </>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              className="rounded-full text-xs h-8 border-green-200 text-green-700 hover:bg-green-50"
                              onClick={() => handleViewAssignedSellers(task.id)}
                            >
                              {task.assignedSellers || 0} Sellers Assigned
                            </Button>
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
          </>
        )}

        {adminSection === 'proofs' && (
          <Card className="border-gray-200 rounded-2xl">
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-gray-900 text-base sm:text-lg">Submitted Proofs & Fraud Probability</CardTitle>
              <CardDescription className="text-xs sm:text-sm">Review proof screenshots, fraud probability, causes, seller trust score, and rating</CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 pt-0">
              <ProofReviewList proofs={sellerMonitor.proofs} />
            </CardContent>
          </Card>
        )}

        <AssignedSellersModal
          isOpen={assignedSellersDialogOpen}
          onClose={() => setAssignedSellersDialogOpen(false)}
          sellers={assignedSellerModalSellers}
          taskInfo={{
            platform: assignedSellersData.task?.platform || '',
            taskType: assignedSellersData.task?.taskType || '',
          }}
          isLoading={isAssignedSellersLoading}
        />

      </div>
    </div>
  );
}
