export interface TreeFileNode {
  type: 'file';
  name: string;
  size: number;
  path: string;
}

export interface TreeDirNode {
  type: 'dir';
  name: string;
  path: string;
  children: TreeNode[];
}

export type TreeNode = TreeFileNode | TreeDirNode;

export interface ArtifactFile {
  path: string;
  size: number;
  truncated: boolean;
  body: string;
  parsed: {
    frontmatter: Record<string, unknown> | null;
    body: string;
    parse_error: string | null;
  };
}
