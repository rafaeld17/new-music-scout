/**
 * API client for Music Scout backend
 */

import type { AlbumAggregate, ReviewItemResponse } from './types';

// In development, use proxy. In production, use environment variable.
const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

export async function fetchRecentAlbums(days = 30, limit = 20): Promise<AlbumAggregate[]> {
  const response = await fetch(`${API_BASE}/albums/recent?days=${days}&limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch recent albums');
  }
  return response.json();
}

export async function fetchTopRatedAlbums(limit = 10, minReviews = 2): Promise<AlbumAggregate[]> {
  const response = await fetch(`${API_BASE}/albums/top-rated?limit=${limit}&min_reviews=${minReviews}`);
  if (!response.ok) {
    throw new Error('Failed to fetch top-rated albums');
  }
  return response.json();
}

export async function fetchControversialAlbums(limit = 10, minReviews = 2): Promise<AlbumAggregate[]> {
  const response = await fetch(`${API_BASE}/albums/controversial?limit=${limit}&min_reviews=${minReviews}`);
  if (!response.ok) {
    throw new Error('Failed to fetch controversial albums');
  }
  return response.json();
}

export async function fetchAlbumById(albumId: number): Promise<AlbumAggregate> {
  const response = await fetch(`${API_BASE}/albums/${albumId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch album');
  }
  return response.json();
}

export async function fetchLatestReviews(limit = 20): Promise<ReviewItemResponse[]> {
  const response = await fetch(`${API_BASE}/reviews/latest?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch latest reviews');
  }
  return response.json();
}

export async function triggerAggregation(): Promise<{ status: string; aggregates_created: number; message: string }> {
  const response = await fetch(`${API_BASE}/aggregate/run`);
  if (!response.ok) {
    throw new Error('Failed to trigger aggregation');
  }
  return response.json();
}
