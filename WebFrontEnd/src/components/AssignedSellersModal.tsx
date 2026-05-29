import { ShieldCheck, Star, UserCheck, Users, X } from 'lucide-react';

type AssignedSeller = {
  id: number | string;
  name: string;
  email: string;
  trust_score: number;
  reputation_score: number;
  proof_status: string;
  audit_status: string;
  rating: number;
  rating_label: string;
  submission_status?: string;
};

type AssignedSellersModalProps = {
  isOpen: boolean;
  onClose: () => void;
  sellers: AssignedSeller[];
  taskInfo: {
    platform: string;
    taskType: string;
  };
  isLoading?: boolean;
};

export default function AssignedSellersModal({
  isOpen,
  onClose,
  sellers,
  taskInfo,
  isLoading = false,
}: AssignedSellersModalProps) {
  if (!isOpen) return null;

  const getInitial = (name: string) => name?.trim()?.charAt(0)?.toUpperCase() || 'S';

  const getAvatarStyle = (rating: number) => {
    let background = '#dc2626';
    if (rating >= 5) background = '#16a34a';
    else if (rating >= 4) background = '#2563eb';
    else if (rating >= 3) background = '#d97706';
    else if (rating >= 2) background = '#ea580c';

    return {
      background,
      color: '#ffffff',
      borderRadius: '9999px',
    };
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 5) return 'bg-green-100 text-green-700 border-green-200';
    if (rating >= 4) return 'bg-blue-100 text-blue-700 border-blue-200';
    if (rating >= 3) return 'bg-amber-100 text-amber-700 border-amber-200';
    if (rating >= 2) return 'bg-orange-100 text-orange-700 border-orange-200';
    return 'bg-red-100 text-red-700 border-red-200';
  };

  const getStatusColor = (status: string) => {
    const value = status?.toLowerCase();

    if (value === 'approved' || value === 'valid' || value === 'passed') {
      return 'bg-green-100 text-green-700 border-green-200';
    }
    if (value === 'pending') {
      return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    }
    if (value === 'rejected' || value === 'invalid' || value === 'violated' || value === 'failed') {
      return 'bg-red-100 text-red-700 border-red-200';
    }
    if (value === 'not_checked') {
      return 'bg-gray-100 text-gray-600 border-gray-200';
    }
    return 'bg-gray-100 text-gray-600 border-gray-200';
  };

  const formatStatus = (status: string) => status?.replaceAll('_', ' ') || 'N/A';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0,0,0,0.55)',
        padding: 16,
      }}
    >
      <div
        className="assigned-sellers-modal"
        style={{
          width: '100%',
          maxWidth: 600,
          height: '80vh',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          background: '#fff',
          borderRadius: 24,
          boxShadow: '0 24px 70px rgba(15,23,42,0.35)',
        }}
      >
        <div
          style={{
            flex: '0 0 auto',
            padding: '20px 22px',
            background: 'linear-gradient(135deg, #0f172a 0%, #0f766e 100%)',
            color: '#fff',
          }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 pr-4">
              <h2 className="text-lg sm:text-xl font-bold text-white">Assigned Sellers</h2>
              <p className="mt-1 truncate text-xs sm:text-sm text-white/80">
                {taskInfo.platform || 'Platform'} - {taskInfo.taskType || 'Task Type'}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-xs font-medium text-white whitespace-nowrap">
                <Users className="h-3.5 w-3.5" />
                {sellers.length} Sellers
              </span>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full p-2 text-white transition hover:bg-white/15"
                aria-label="Close assigned sellers modal"
                style={{ border: '1px solid rgba(255,255,255,0.25)' }}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        <div
          className="assigned-sellers-scroll"
          style={{
            flex: '1 1 auto',
            minHeight: 0,
            overflowY: 'scroll',
            overflowX: 'hidden',
            padding: 16,
          }}
        >
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-14 text-center">
              <div className="mb-3 h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-teal-600" />
              <p className="text-sm text-gray-500">Loading assigned sellers...</p>
            </div>
          ) : sellers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-14 text-center">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100 text-gray-500">
                <UserCheck className="h-7 w-7" />
              </div>
              <h3 className="text-base font-semibold text-gray-900">No sellers assigned yet</h3>
              <p className="mt-1 text-sm text-gray-500">Assigned sellers will appear here once available.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sellers.map((seller) => (
                <div
                  key={seller.id}
                  className="rounded-xl border border-gray-200 bg-white p-3 sm:p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="flex gap-3 sm:gap-4">
                    <div
                      className="flex h-10 w-10 sm:h-12 sm:w-12 shrink-0 items-center justify-center text-sm sm:text-base font-bold"
                      style={getAvatarStyle(Number(seller.rating))}
                    >
                      {getInitial(seller.name)}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="break-words text-sm sm:text-base font-semibold leading-snug text-gray-900">{seller.name}</h3>
                          <p className="break-all text-xs sm:text-sm text-gray-500">{seller.email}</p>
                        </div>
                        <span
                          className={`hidden sm:inline-flex shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold whitespace-nowrap ${getRatingColor(
                            Number(seller.rating),
                          )}`}
                        >
                          {seller.rating_label}
                        </span>
                      </div>

                      <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
                        <div className="flex min-w-0 items-center gap-2 rounded-lg bg-gray-50 px-3 py-2">
                          <ShieldCheck className="h-4 w-4 shrink-0 text-teal-600" />
                          <span className="text-xs text-gray-500">Trust</span>
                          <span className="ml-auto text-sm font-semibold text-gray-900 whitespace-nowrap">
                            {Number(seller.trust_score).toFixed(2)}
                          </span>
                        </div>
                        <div className="flex min-w-0 items-center gap-2 rounded-lg bg-gray-50 px-3 py-2">
                          <Star className="h-4 w-4 shrink-0 text-amber-500" />
                          <span className="truncate text-xs text-gray-500">Reputation</span>
                          <span className="ml-auto text-sm font-semibold text-gray-900 whitespace-nowrap">
                            {Number(seller.reputation_score).toFixed(2)}
                          </span>
                        </div>
                      </div>

                      <div className="mt-4 border-t border-gray-100 pt-3 flex flex-wrap gap-2">
                        <span
                          className={`rounded-full border px-2 py-1 text-xs font-medium leading-none whitespace-nowrap ${getRatingColor(
                            Number(seller.rating),
                          )}`}
                        >
                          {seller.rating_label}
                        </span>
                        <span className={`rounded-full border px-2 py-1 text-xs font-medium leading-none whitespace-nowrap ${getStatusColor(seller.proof_status)}`}>
                          Proof: {formatStatus(seller.proof_status)}
                        </span>
                        <span className={`rounded-full border px-2 py-1 text-xs font-medium leading-none whitespace-nowrap ${getStatusColor(seller.audit_status)}`}>
                          Audit: {formatStatus(seller.audit_status)}
                        </span>
                        {seller.submission_status && (
                          <span
                            className={`rounded-full border px-2 py-1 text-xs font-medium leading-none whitespace-nowrap ${getStatusColor(
                              seller.submission_status,
                            )}`}
                          >
                            {formatStatus(seller.submission_status)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
