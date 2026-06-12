export const API_URL = (typeof window === 'undefined' ? process.env.INTERNAL_API_URL : undefined) ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export type Paper = {
  id: number;
  title: string;
  abstract: string;
  authors: string[];
  categories: string[];
  published_at: string;
  pdf_url: string;
  citation_count: number;
  cluster_id?: number;
};

export type Dashboard = {
  project: { id: number; topic: string; status: string };
  total_papers: number;
  number_of_clusters: number;
  emerging_topics: string[];
  citation_leaders: Paper[];
  research_opportunities: { opportunity: string; reason: string; score: number; evidence: Record<string, unknown> }[];
  recent_papers: Paper[];
  papers_per_month: { month: string; papers: number }[];
  growth_rate: number;
};

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, cache: 'no-store' });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
