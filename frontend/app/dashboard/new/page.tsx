import { redirect } from 'next/navigation';
import { fetchJson } from '@/lib/api';

export default async function NewDashboard({ searchParams }: { searchParams: { topic?: string } }) {
  const topic = searchParams.topic ?? 'Large Language Models';
  const project = await fetchJson<{ id: number }>('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, max_papers: 100 })
  });
  redirect(`/dashboard/${project.id}`);
}
