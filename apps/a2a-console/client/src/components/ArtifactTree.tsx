import { ChevronRight, FileText, Folder } from 'lucide-react';
import { useState } from 'react';

import { cn } from '@/lib/cn';
import { formatSize } from '@/lib/format';
import type { TreeNode } from '@/types/artifact';

interface ArtifactTreeProps {
  nodes: TreeNode[];
  selectedPath?: string | null;
  onSelect?: (path: string) => void;
}

export function ArtifactTree({ nodes, selectedPath, onSelect }: ArtifactTreeProps) {
  return (
    <ul className="space-y-0.5 text-sm">
      {nodes.map((n) => (
        <TreeItem key={n.path} node={n} depth={0} selectedPath={selectedPath} onSelect={onSelect} />
      ))}
    </ul>
  );
}

function TreeItem({
  node,
  depth,
  selectedPath,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedPath?: string | null;
  onSelect?: (path: string) => void;
}) {
  const [open, setOpen] = useState(true);
  if (node.type === 'dir') {
    return (
      <li>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex w-full items-center gap-1 rounded px-1.5 py-1 text-left hover:bg-muted"
          style={{ paddingLeft: depth * 12 + 6 }}
        >
          <ChevronRight className={cn('h-3 w-3 text-muted-foreground transition-transform', open && 'rotate-90')} />
          <Folder className="h-3.5 w-3.5 text-amber-600" />
          <span className="truncate font-medium">{node.name}</span>
        </button>
        {open ? (
          <ul className="space-y-0.5">
            {node.children.map((c) => (
              <TreeItem
                key={c.path}
                node={c}
                depth={depth + 1}
                selectedPath={selectedPath}
                onSelect={onSelect}
              />
            ))}
          </ul>
        ) : null}
      </li>
    );
  }
  const isSelected = selectedPath === node.path;
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect?.(node.path)}
        className={cn(
          'flex w-full items-center gap-1 rounded px-1.5 py-1 text-left hover:bg-muted',
          isSelected && 'bg-sky-100 text-sky-900 hover:bg-sky-100',
        )}
        style={{ paddingLeft: depth * 12 + 18 }}
      >
        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="flex-1 truncate">{node.name}</span>
        <span className="text-[10px] text-muted-foreground">{formatSize(node.size)}</span>
      </button>
    </li>
  );
}
