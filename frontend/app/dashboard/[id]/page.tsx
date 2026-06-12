import { CitationGraph } from '@/components/CitationGraph';
import { MetricCard } from '@/components/MetricCard';
import { TrendChart } from '@/components/TrendChart';
import { Dashboard, fetchJson } from '@/lib/api';

export default async function DashboardPage({ params }: { params: { id: string } }) {
  const dashboard = await fetchJson<Dashboard>(`/api/projects/${params.id}/dashboard`);
  const clusters = await fetchJson<{ id: number; name: string; summary: string; keywords: string[]; paper_count: number }[]>(`/api/projects/${params.id}/clusters`);
  const graph = await fetchJson<{ nodes: { id: string; label: string }[]; edges: { id: string; source: string; target: string }[] }>(`/api/projects/${params.id}/graph`);
  const evaluation = await fetchJson<{ semantic_search: Record<string, number | string>; clustering: Record<string, number>; recommendations: Record<string, unknown> }>(`/api/projects/${params.id}/evaluation`);

  return (
    <main className="min-h-screen px-6 py-8">
      <section className="mx-auto max-w-7xl space-y-8">
        <header className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-violet-300">Research Intelligence</p>
            <h1 className="mt-2 text-4xl font-bold text-white">{dashboard.project.topic}</h1>
            <p className="mt-2 text-slate-300">Status: {dashboard.project.status}. Explore clusters, trends, gaps, citation structure, recommendations, and evaluation.</p>
          </div>
          <a href="/" className="rounded-full border border-white/10 px-4 py-2 text-sm">New topic</a>
        </header>

        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Total papers" value={dashboard.total_papers} detail="ArXiv records indexed locally" />
          <MetricCard label="Clusters" value={dashboard.number_of_clusters} detail="UMAP/HDBSCAN with fallback" />
          <MetricCard label="Growth rate" value={`${dashboard.growth_rate}%`} detail="First-to-last month change" />
          <MetricCard label="Precision@K" value={String(evaluation.semantic_search.precision_at_k)} detail="Search evaluation estimate" />
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.3fr_.7fr]">
          <TrendChart data={dashboard.papers_per_month} />
          <div className="rounded-3xl glass p-5">
            <h2 className="text-lg font-semibold">Fastest Growing Topics</h2>
            <ol className="mt-4 space-y-3">{dashboard.emerging_topics.map((topic, i) => <li className="rounded-2xl bg-white/5 p-3" key={topic}>{i + 1}. {topic}</li>)}</ol>
          </div>
        </div>

        <section className="grid gap-4 lg:grid-cols-3">
          {dashboard.research_opportunities.map((gap) => (
            <article className="rounded-3xl glass p-5" key={gap.opportunity}>
              <div className="flex items-center justify-between"><h3 className="font-semibold text-white">{gap.opportunity}</h3><span className="rounded-full bg-emerald-400/15 px-3 py-1 text-emerald-200">{gap.score}/10</span></div>
              <p className="mt-3 text-sm text-slate-300">{gap.reason}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-3xl glass p-5">
            <h2 className="text-xl font-semibold">Automatic Research Clusters</h2>
            <div className="mt-4 space-y-3">{clusters.map((cluster) => <div className="rounded-2xl bg-white/5 p-4" key={cluster.id}><div className="flex justify-between"><h3 className="font-semibold">{cluster.name}</h3><span>{cluster.paper_count} papers</span></div><p className="mt-2 text-sm text-slate-300">{cluster.summary}</p><div className="mt-3 flex flex-wrap gap-2">{cluster.keywords.slice(0, 6).map((kw) => <span className="rounded-full bg-violet-400/10 px-2 py-1 text-xs text-violet-200" key={kw}>{kw}</span>)}</div></div>)}</div>
          </div>
          <div className="rounded-3xl glass p-5">
            <h2 className="text-xl font-semibold">Recent Papers</h2>
            <div className="mt-4 space-y-3">{dashboard.recent_papers.map((paper) => <a className="block rounded-2xl bg-white/5 p-4 hover:bg-white/10" href={paper.pdf_url} key={paper.id}><h3 className="font-medium text-white">{paper.title}</h3><p className="mt-1 text-xs text-slate-400">{new Date(paper.published_at).toLocaleDateString()} · {paper.categories.join(', ')}</p></a>)}</div>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold">Citation and Similarity Communities</h2>
          <CitationGraph graph={graph} />
        </section>
      </section>
    </main>
  );
}
