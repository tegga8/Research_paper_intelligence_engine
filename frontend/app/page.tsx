import Link from 'next/link';
import { Brain, Network, Search, Sparkles } from 'lucide-react';

const examples = ['Large Language Models', 'Reinforcement Learning', 'Computer Vision', 'Time Series Forecasting', 'AI for Agriculture'];

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto max-w-6xl">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-xl font-semibold"><Brain className="text-violet-300" /> Research Paper Intelligence Engine</div>
          <Link className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200" href="/dashboard/1">Demo dashboard</Link>
        </nav>
        <div className="mt-24 grid gap-10 lg:grid-cols-[1.1fr_.9fr] lg:items-center">
          <div>
            <p className="mb-4 inline-flex rounded-full border border-violet-300/30 bg-violet-400/10 px-4 py-2 text-sm text-violet-200">ArXiv field intelligence, not another chatbot</p>
            <h1 className="text-5xl font-bold tracking-tight text-white md:text-7xl">Map a research field in minutes.</h1>
            <p className="mt-6 max-w-2xl text-lg text-slate-300">Discover papers, cluster research directions, identify emerging trends, generate literature reviews, and surface high-value research gaps from ArXiv collections.</p>
            <form action="/dashboard/new" className="mt-8 flex flex-col gap-3 rounded-3xl glass p-3 sm:flex-row">
              <input name="topic" placeholder="Try: RAG evaluation or AI for agriculture" className="min-h-14 flex-1 rounded-2xl border border-white/10 bg-slate-950/80 px-5 outline-none" />
              <button className="rounded-2xl bg-violet-500 px-6 font-semibold text-white hover:bg-violet-400">Build dashboard</button>
            </form>
            <div className="mt-5 flex flex-wrap gap-2">{examples.map((example) => <span className="rounded-full bg-white/10 px-3 py-1 text-sm text-slate-300" key={example}>{example}</span>)}</div>
          </div>
          <div className="grid gap-4">
            {[['Semantic Search', Search], ['Research Gap Finder', Sparkles], ['Citation Communities', Network]].map(([label, Icon]) => {
              const C = Icon as typeof Search;
              return <div className="rounded-3xl glass p-6" key={String(label)}><C className="mb-4 text-violet-300" /><h3 className="text-xl font-semibold">{String(label)}</h3><p className="mt-2 text-slate-300">Explainable insights with citations, nearest neighbors, and evidence trails.</p></div>;
            })}
          </div>
        </div>
      </section>
    </main>
  );
}
