import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import SellerDashboard from './SellerDashboard';

vi.mock('./ConnectSocial', () => ({
  default: ({ sellerId }: { sellerId: number }) => (
    <div data-testid="connect-social">Connect social for seller {sellerId}</div>
  ),
}));

const tasks = [
  {
    id: 10,
    platform: 'Instagram',
    title: 'Like Instagram Post',
    type: 'Like',
    timeEstimate: '2 min',
    difficulty: 'Easy',
    remaining: 4,
    total: 10,
    price: 1.25,
    url: 'https://www.instagram.com/p/test',
  },
  {
    id: 11,
    platform: 'YouTube',
    title: 'Watch Product Video',
    type: 'Watch',
    timeEstimate: '5 min',
    difficulty: 'Easy',
    remaining: 2,
    total: 8,
    price: 2,
    url: 'https://youtu.be/abcdefghijk',
  },
];

const stats = {
  walletBalance: 12.5,
  totalEarnings: 40,
  tasksCompleted: 7,
  inProgress: 2,
  successRate: 91,
  avgCompletionTime: 4,
  rating: 4,
  ratingLabel: '4 Star',
  performanceScore: 82.25,
  finalReputationScore: 79.9,
  trustScore: 74.5,
  myTasks: [
    {
      id: 20,
      platform: 'Facebook',
      title: 'Comment on Page',
      submitted: 'Today',
      earnings: 1.5,
      status: 'pending',
    },
  ],
};

function mockFetch() {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url.includes('/api/approved-tasks/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ tasks }),
      } as Response);
    }

    if (url.includes('/api/seller-dashboard-stats/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(stats),
      } as Response);
    }

    if (url.includes('/api/submit-task/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ message: 'Task submitted successfully' }),
      } as Response);
    }

    return Promise.reject(new Error(`Unhandled fetch URL: ${url}`));
  });
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <SellerDashboard
        userData={{ userId: 99, userName: 'Ali' }}
        onLogout={vi.fn()}
      />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch());
  vi.stubGlobal('open', vi.fn());
  vi.stubGlobal('alert', vi.fn());
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
});

describe('SellerDashboard', () => {
  it('renders seller stats and assigned tasks from the API', async () => {
    renderDashboard();

    expect(await screen.findByText('Welcome back, Ali!')).toBeInTheDocument();
    expect(await screen.findByText('Like Instagram Post')).toBeInTheDocument();
    expect(screen.getByText('Watch Product Video')).toBeInTheDocument();
    expect(screen.getAllByText('$12.50')).toHaveLength(2);
    expect(screen.getAllByText('4 Star')).toHaveLength(2);
    expect(screen.getByText('79.90 / 100')).toBeInTheDocument();
    expect(screen.getByText('82.25 / 100')).toBeInTheDocument();
    expect(screen.getByText('74.50 / 100')).toBeInTheDocument();
    expect(screen.getByText('Connect social for seller 99')).toBeInTheDocument();
  });

  it('opens a non-YouTube task URL in a new tab and shows the proof dialog', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await screen.findByText('Like Instagram Post');
    await user.click(screen.getAllByRole('button', { name: /start task/i })[0]);

    expect(window.open).toHaveBeenCalledWith(
      'https://www.instagram.com/p/test',
      '_blank',
      'noopener,noreferrer',
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Complete Task')).toBeInTheDocument();
    expect(screen.getByText('- The task has been opened in a new browser tab.')).toBeInTheDocument();
  });

  it('opens YouTube tasks in the drawer instead of a new tab', async () => {
    renderDashboard();

    await screen.findByText('Watch Product Video');
    const startButtons = screen.getAllByRole('button', { name: /start task/i });
    fireEvent.click(startButtons[1]);

    expect(window.open).not.toHaveBeenCalled();
    expect(screen.getByText('YouTube Task')).toBeInTheDocument();
    expect(screen.getByText('Watch at least 70% to unlock close button')).toBeInTheDocument();
  });

  it('fetches seller data once on mount', async () => {
    renderDashboard();

    await screen.findByText('Like Instagram Post');

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });
});
