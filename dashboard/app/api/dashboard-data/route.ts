import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/dashboard-data`, {
      cache: 'no-store'
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching from backend:', error);
    return NextResponse.json({ error: 'Failed to fetch data' }, { status: 500 });
  }
}
