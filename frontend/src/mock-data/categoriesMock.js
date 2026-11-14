export const MOCK_CATEGORIES = [
  { id: 1, name: 'Cloud & Infrastructure', code: 'CAT-CLOUD' },
  { id: 2, name: 'Cybersecurity & Compliance', code: 'CAT-SEC' },
  { id: 3, name: 'Data Analytics & AI', code: 'CAT-DATA' },
  { id: 4, name: 'Hardware Appliances', code: 'CAT-HW' },
  { id: 5, name: 'Professional Services & Support', code: 'CAT-SRV' },
];

export const MOCK_REGIONS = [
  { id: 1, name: 'North America - East', code: 'NA-EAST', country: 'United States', state: 'New York', city: 'New York' },
  { id: 2, name: 'North America - West', code: 'NA-WEST', country: 'United States', state: 'California', city: 'San Francisco' },
  { id: 3, name: 'North America - Central', code: 'NA-CENTRAL', country: 'United States', state: 'Illinois', city: 'Chicago' },
  { id: 4, name: 'Europe - UK & Ireland', code: 'EU-WEST', country: 'United Kingdom', state: 'England', city: 'London' },
  { id: 5, name: 'Europe - Central', code: 'EU-CENTRAL', country: 'Germany', state: 'Hesse', city: 'Frankfurt' },
  { id: 6, name: 'Asia Pacific - Japan', code: 'APAC-JP', country: 'Japan', state: 'Kanto', city: 'Tokyo' },
  { id: 7, name: 'Asia Pacific - ANZ', code: 'APAC-ANZ', country: 'Australia', state: 'New South Wales', city: 'Sydney' },
  { id: 8, name: 'Latin America', code: 'LATAM', country: 'Brazil', state: 'São Paulo', city: 'São Paulo' }
];

export const MOCK_FILTER_OPTIONS = {
  categories: MOCK_CATEGORIES,
  regions: MOCK_REGIONS,
  segments: ['Enterprise', 'Mid-Market', 'SMB', 'Direct Consumer'],
  payment_methods: ['Wire Transfer', 'Credit Card', 'ACH', 'PayPal'],
  min_date: '2024-06-01',
  max_date: '2026-11-14'
};
