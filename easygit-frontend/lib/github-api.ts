const GITHUB_TOKEN = process.env.NEXT_PUBLIC_GITHUB_TOKEN || '';
const GITHUB_API_BASE = 'https://api.github.com';

export interface GitHubFile {
  name: string;
  path: string;
  type: 'file' | 'dir';
  size?: number;
  download_url?: string;
  url: string;
}

export interface FileTreeItem {
  name: string;
  type: 'folder' | 'file';
  path: string;
  size?: number;
  icon?: React.ComponentType;
  children?: FileTreeItem[];
}

class GitHubAPI {
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private async makeRequest(url: string): Promise<any> {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitDocify-App'
      }
    });

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getRepositoryContents(owner: string, repo: string, path: string = ''): Promise<GitHubFile[]> {
    const url = `${GITHUB_API_BASE}/repos/${owner}/${repo}/contents/${path}`;
    return this.makeRequest(url);
  }

  async buildFileTree(owner: string, repo: string, path: string = ''): Promise<FileTreeItem[]> {
    try {
      const contents = await this.getRepositoryContents(owner, repo, path);
      const tree: FileTreeItem[] = [];

      // Sort contents: folders first, then files
      const sortedContents = contents.sort((a, b) => {
        if (a.type === 'dir' && b.type === 'file') return -1;
        if (a.type === 'file' && b.type === 'dir') return 1;
        return a.name.localeCompare(b.name);
      });

      for (const item of sortedContents) {
        const treeItem: FileTreeItem = {
          name: item.name,
          type: item.type === 'dir' ? 'folder' : 'file',
          path: item.path,
          size: item.size,
        };

        // For folders, recursively get children (limit depth to avoid too many API calls)
        if (item.type === 'dir' && this.shouldLoadFolder(item.path)) {
          try {
            treeItem.children = await this.buildFileTree(owner, repo, item.path);
          } catch (error) {
            console.warn(`Failed to load folder ${item.path}:`, error);
            treeItem.children = [];
          }
        }

        tree.push(treeItem);
      }

      return tree;
    } catch (error) {
      console.error(`Error building file tree for ${owner}/${repo}:`, error);
      throw error;
    }
  }

  private shouldLoadFolder(path: string): boolean {
    // Skip common folders that are typically large or not needed
    const skipFolders = [
      'node_modules',
      '.git',
      '.next',
      'dist',
      'build',
      'target',
      'vendor',
      '__pycache__',
      '.pytest_cache',
      '.mypy_cache',
      'coverage',
      '.vscode',
      '.idea'
    ];

    const folderName = path.split('/').pop() || '';
    return !skipFolders.includes(folderName) && path.split('/').length < 4; // Limit depth
  }

  async getRepositoryInfo(owner: string, repo: string) {
    const url = `${GITHUB_API_BASE}/repos/${owner}/${repo}`;
    const repoData = await this.makeRequest(url);
    
    // Also get the latest commit info
    const commitsUrl = `${GITHUB_API_BASE}/repos/${owner}/${repo}/commits/${repoData.default_branch}`;
    try {
      const latestCommit = await this.makeRequest(commitsUrl);
      return {
        ...repoData,
        sha: latestCommit.sha,
        latest_commit: latestCommit
      };
    } catch (error) {
      // If we can't get the latest commit, return repo data without it
      return repoData;
    }
  }
}

export const githubAPI = new GitHubAPI(GITHUB_TOKEN);
