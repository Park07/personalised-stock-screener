// __tests__/CompanyDetail.test.jsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi } from 'vitest';
import CompanyDetail from '../src/page/CompanyDetail';
import '@testing-library/jest-dom';

// Mock necessary dependencies
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn().mockReturnValue({ ticker: 'TEST' }),
    useLocation: vi.fn().mockReturnValue({
      search: '?goal=value&risk=moderate&sector=Technology'
    }),
    useNavigate: vi.fn().mockReturnValue(vi.fn())
  };
});

// Constants for testing
const MOCK_TICKER = 'TEST';
const MOCK_COMPANY_DATA = {
  companies: [
    {
      ticker: MOCK_TICKER,
      company_name: 'Test Inc. from Rank',
      sector: 'Technology',
      website: 'http://test-rank.com',
      market_cap: 1050000000000,
      current_price: 151,
      valuation_score: 4.1,
      growth_score: 3.8,
      health_score: 4.5,
      overall_score: 4,
      pe_ratio: 25.5,
      dividend_yield: 0.01
    }
  ]
};

// Setup and tear down
beforeEach(() => {
  vi.clearAllMocks();
});

// Helper function to render the component within router context
const renderComponent = () => {
  return render(
    <MemoryRouter initialEntries={[`/company/${MOCK_TICKER}?goal=value&risk=moderate&sector=Technology`]}>
      <Routes>
        <Route path="/company/:ticker" element={<CompanyDetail />} />
      </Routes>
    </MemoryRouter>
  );
};

describe('CompanyDetail Component', () => {
  
  // Test 1: Should display loading state initially
  it('should display loading state initially', async () => {
    // Mock the global fetch to delay returning
    global.fetch = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 500)));
    
    renderComponent();
    
    // Check if loading indicator is present
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
    
    // Clean up
    global.fetch.mockRestore();
  });
  
  // Test 3: Should display error message on failed rank data fetch
  it('should display error message on failed rank data fetch', async () => {
    // Mock fetch to fail for rank data
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/api/rank')) {
        return Promise.reject(new Error('Network Error for Rank'));
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(MOCK_COMPANY_DATA)
      });
    });
    
    renderComponent();
    
    // Wait for the error message to appear
    await waitFor(() => {
      expect(screen.getByText(/Error Loading Company Data/i)).toBeInTheDocument();
    });
    
    // Clean up
    global.fetch.mockRestore();
  });
  

});