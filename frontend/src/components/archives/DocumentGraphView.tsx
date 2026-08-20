import { useNavigate } from 'react-router-dom';
import type { DocumentGraph } from '../../api/types';

export function DocumentGraphView({ graph, centerDocumentId }: { graph: DocumentGraph; centerDocumentId: string }) {
  const navigate = useNavigate();
  const size = 360;
  const center = size / 2;
  const radius = size / 2 - 56;

  const centerNode = graph.nodes.find((n) => n.document_id === centerDocumentId) ?? graph.nodes[0];
  const others = graph.nodes.filter((n) => n.id !== centerNode?.id);

  const positions = new Map<string, { x: number; y: number }>();
  if (centerNode) positions.set(centerNode.id, { x: center, y: center });
  others.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(others.length, 1);
    positions.set(node.id, {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    });
  });

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label="Legal knowledge graph showing document relationships"
    >
      {graph.edges.map((edge, i) => {
        const from = positions.get(edge.source);
        const to = positions.get(edge.target);
        if (!from || !to) return null;
        return (
          <line
            key={i}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            stroke="var(--card-border)"
            strokeWidth={1.5}
          />
        );
      })}
      {graph.nodes.map((node) => {
        const pos = positions.get(node.id);
        if (!pos) return null;
        const isCenter = node.id === centerNode?.id;
        const isNavigable = !isCenter && Boolean(node.document_id);
        return (
          <g
            key={node.id}
            transform={`translate(${pos.x}, ${pos.y})`}
            role={isNavigable ? 'button' : undefined}
            tabIndex={isNavigable ? 0 : undefined}
            aria-label={isNavigable ? `Open ${node.name}` : node.name}
            onClick={() => isNavigable && navigate(`/archives/documents/${node.document_id}`)}
            onKeyDown={(e) => {
              if (isNavigable && (e.key === 'Enter' || e.key === ' ')) navigate(`/archives/documents/${node.document_id}`);
            }}
            className={isNavigable ? 'cursor-pointer' : ''}
          >
            <circle
              r={isCenter ? 10 : 7}
              fill={isCenter ? 'var(--accent-gold)' : isNavigable ? 'var(--ink)' : 'var(--ink-muted)'}
            />
            <text x={0} y={isCenter ? -16 : -12} textAnchor="middle" fontSize={10} fill="var(--ink-muted)">
              {node.name.length > 22 ? `${node.name.slice(0, 22)}…` : node.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
