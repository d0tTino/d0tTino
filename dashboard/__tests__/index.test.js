jest.mock('@tauri-apps/api/tauri', () => ({ __esModule: true, invoke: jest.fn() }), { virtual: true });
jest.mock('@tauri-apps/api/event', () => ({ __esModule: true, listen: jest.fn(() => Promise.resolve(() => {})) }), { virtual: true });

import { render, screen, fireEvent } from '@testing-library/react';
import Home from '../pages/index';
import { invoke } from '@tauri-apps/api/tauri';

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    if (url === '/api/health') {
      return Promise.resolve({ json: () => Promise.resolve({ status: 'ok' }) });
    }
    if (url === '/api/stats') {
      return Promise.resolve({ json: () => Promise.resolve({ queries: 1, memory: 2 }) });
    }
    if (url === '/api/prompt') {
      return Promise.resolve({ json: () => Promise.resolve({ response: 'hello' }) });
    }
    return Promise.resolve({ json: () => Promise.resolve({}) });
  });
});

afterEach(() => {
  jest.resetAllMocks();
});

test('fetches health and stats on mount', async () => {
  render(<Home />);
  expect(fetch).toHaveBeenCalledWith('/api/health');
  expect(fetch).toHaveBeenCalledWith('/api/stats');
  expect(await screen.findByText('API status: ok')).toBeInTheDocument();
  expect(await screen.findByText(/Queries: 1, Memory: 2/)).toBeInTheDocument();
});

test('sends prompt and displays response', async () => {
  render(<Home />);
  fireEvent.change(screen.getByPlaceholderText('prompt'), { target: { value: 'test' } });
  fireEvent.click(screen.getByText('Send'));
  expect(fetch).toHaveBeenCalledWith(
    '/api/prompt',
    expect.objectContaining({ method: 'POST' })
  );
  expect(await screen.findByText('hello')).toBeInTheDocument();
});

test('getPlan invokes backend and updates tasks', async () => {
  render(<Home />);
  window.__TAURI__ = {};
  invoke.mockResolvedValue(['demo']);
  fireEvent.change(screen.getByPlaceholderText('goal'), { target: { value: 'demo' } });
  fireEvent.click(screen.getByText('Plan'));
  expect(invoke).toHaveBeenCalledWith('plan', { goal: 'demo' });
  expect(await screen.findByText('demo')).toBeInTheDocument();
});
