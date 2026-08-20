import { useNavigate } from 'react-router-dom';
import type { DocumentGraph } from '../../api/types';

export function DocumentGraphView({ graph, centerId }: { graph: DocumentGraph; centerId: string }) {
  const navigate = useNavigate();
  const size = 360;
  const center = size / 2;
  const radius = size / 2 - 48;
  const others = graph.nodes.filter((n) => n.id !== centerId);

  const positions = new Map<string, { x: number; y: number }>();
  positions.set(centerId, { x: center, y: center });
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
        const isCenter = node.id === centerId;
        return (
          <g
            key={node.id}
            transform={`translate(${pos.x}, ${pos.y})`}
            role="button"
            tabIndex={0}
            aria-label={`Open ${node.label}`}
            onClick={() => !isCenter && navigate(`/archives/documents/${node.id}`)}
            onKeyDown={(e) => {
              if ((e.key === 'Enter' || e.key === ' ') && !isCenter) navigate(`/archives/documents/${node.id}`);
            }}
            className={isCenter ? '' : 'cursor-pointer'}
          >
            <circle r={isCenter ? 10 : 7} fill={isCenter ? 'var(--accent-gold)' : 'var(--ink)'} />
            <text
              x={0}
              y={isCenter ? -16 : -12}
              textAnchor="middle"
              fontSize={10}
              fill="var(--ink-muted)"
            >
              {node.label.length > 22 ? `${node.label.slice(0, 22)}…` : node.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
