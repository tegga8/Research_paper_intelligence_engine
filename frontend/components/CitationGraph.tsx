'use client';
import { Background, Controls, MiniMap, ReactFlow } from '@xyflow/react';
import ReactFlow, { Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export function CitationGraph({ graph }: { graph: { nodes: { id: string; label: string; cluster?: number }[]; edges: { id: string; source: string; target: string }[] } }) {
  const nodes = graph.nodes.slice(0, 80).map((node, index) => ({
    id: node.id,
    data: { label: node.label },
    position: { x: (index % 10) * 180, y: Math.floor(index / 10) * 110 },
    style: { background: '#111827', color: '#e5e7eb', border: '1px solid #7c3aed', borderRadius: 16, width: 150 }
  }));
  return (
    <div className="h-[32rem] rounded-3xl glass overflow-hidden">
      <ReactFlow nodes={nodes} edges={graph.edges.slice(0, 140)} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
