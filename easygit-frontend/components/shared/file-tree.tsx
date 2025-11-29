"use client";
import React, { useState, useEffect } from "react";
import useTutorialStore from "@/store/tutorialstore";
import { Box } from "lucide-react";

export interface FileTreeItem {
  name: string;
  type: "folder" | "file";
  path: string;
  size?: number;
  icon?: React.ComponentType;
  children?: FileTreeItem[];
}

export interface RepositoryMetadata {
  owner: string;
  repository: string;
  requestedRef: string;
  resolvedCommit: string;
  path: string;
  maxSize: string;
}

interface FileTreeProps {
  fileTreeData?: FileTreeItem[];
}

interface FolderIconProps {
  isOpen: boolean;
}

interface ChevronIconProps {
  isOpen: boolean;
}

interface TreeIconProps {
  item: FileTreeItem;
  isOpen: boolean;
}

interface TreeNodeProps {
  item: FileTreeItem;
  path?: string;
}

const FileIcon = () => (
  <svg
    className="w-5 h-5 mr-2 text-gray-500 dark:text-gray-400 shrink-0"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
    />
  </svg>
);
const JsIcon = () => (
  <svg
    className="w-5 h-5 mr-2 shrink-0"
    xmlns="http://www.w3.org/2000/svg"
    x="0px"
    y="0px"
    viewBox="0 0 48 48"
  >
    <path fill="#ffd600" d="M6,42V6h36v36H6z"></path>
    <path
      fill="none"
      stroke="#000001"
      strokeMiterlimit="10"
      strokeWidth="3.3"
      d="M23.783,22.352v9.819 c0,3.764-4.38,4.022-6.283,0.802"
    ></path>
    <path
      fill="none"
      stroke="#000001"
      strokeMiterlimit="10"
      strokeWidth="3.3"
      d="M34.69,25.343 c-1.739-2.727-5.674-2.345-5.84,0.558c-0.214,3.757,6.768,2.938,6.247,7.107c-0.365,2.92-4.874,3.858-7.193-0.065"
    ></path>
  </svg>
);
const HtmlIcon = () => (
  <svg
    className="w-5 h-5 mr-2 shrink-0"
    xmlns="http://www.w3.org/2000/svg"
    x="0px"
    y="0px"
    viewBox="0 0 48 48"
  >
    <path fill="#E65100" d="M41,5H7l3,34l14,4l14-4L41,5L41,5z"></path>
    <path fill="#FF6D00" d="M24 8L24 39.9 35.2 36.7 37.7 8z"></path>
    <path
      fill="#FFF"
      d="M24,25v-4h8.6l-0.7,11.5L24,35.1v-4.2l4.1-1.4l0.3-4.5H24z M32.9,17l0.3-4H24v4H32.9z"
    ></path>
    <path
      fill="#EEE"
      d="M24,30.9v4.2l-7.9-2.6L15.7,27h4l0.2,2.5L24,30.9z M19.1,17H24v-4h-9.1l0.7,12H24v-4h-4.6L19.1,17z"
    ></path>
  </svg>
);
const CssIcon = () => (
  <svg
    className="w-5 h-5 mr-2 shrink-0"
    xmlns="http://www.w3.org/2000/svg"
    x="0px"
    y="0px"
    viewBox="0 0 48 48"
  >
    <path fill="#0277BD" d="M41,5H7l3,34l14,4l14-4L41,5L41,5z"></path>
    <path fill="#039BE5" d="M24 8L24 39.9 35.2 36.7 37.7 8z"></path>
    <path
      fill="#FFF"
      d="M33.1 13L24 13 24 17 28.9 17 28.6 21 24 21 24 25 28.4 25 28.1 29.5 24 30.9 24 35.1 31.9 32.5 32.6 21 32.6 21z"
    ></path>
    <path
      fill="#EEE"
      d="M24,13v4h-8.9l-0.3-4H24z M19.4,21l0.2,4H24v-4H19.4z M19.8,27h-4l0.3,5.5l7.9,2.6v-4.2l-4.1-1.4L19.8,27z"
    ></path>
  </svg>
);
const ReactIcon = () => (
  <svg
    className="w-5 h-5 mr-2 text-cyan-400 shrink-0"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="2" fill="currentColor" />
    <g>
      <ellipse
        cx="12"
        cy="12"
        rx="11"
        ry="4.2"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <ellipse
        cx="12"
        cy="12"
        rx="11"
        ry="4.2"
        transform="rotate(60 12 12)"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <ellipse
        cx="12"
        cy="12"
        rx="11"
        ry="4.2"
        transform="rotate(120 12 12)"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </g>
  </svg>
);

const FolderIcon: React.FC<FolderIconProps> = ({ isOpen }) => (
  <svg
    className="w-5 h-5 mr-2 text-yellow-500 shrink-0"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    {isOpen ? (
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
        d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
      />
    ) : (
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
        d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
      />
    )}
  </svg>
);

const ChevronIcon: React.FC<ChevronIconProps> = ({ isOpen }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    fill="currentColor"
    className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform duration-200 shrink-0 ${isOpen ? "rotate-90" : ""}`}
  >
    <path
      fillRule="evenodd"
      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
      clipRule="evenodd"
    />
  </svg>
);

const defaultFileTreeData: FileTreeItem[] = [
  {
    name: "public",
    type: "folder",
    path: "public",
    children: [
      { name: "index.html", type: "file", path: "public/index.html" },
      { name: "favicon.ico", type: "file", path: "public/favicon.ico" },
    ],
  },
  {
    name: "src",
    type: "folder",
    path: "src",
    children: [
      {
        name: "components",
        type: "folder",
        path: "src/components",
        children: [
          { name: "Button.jsx", type: "file", path: "src/components/Button.jsx", icon: ReactIcon },
          { name: "Modal.js", type: "file", path: "src/components/Modal.js" },
        ],
      },
      {
        name: "hooks",
        type: "folder",
        path: "src/hooks",
        children: [{ name: "useFetch.js", type: "file", path: "src/hooks/useFetch.js" }],
      },
      { name: "App.jsx", type: "file", path: "src/App.jsx", icon: ReactIcon },
      { name: "index.js", type: "file", path: "src/index.js" },
      { name: "styles.css", type: "file", path: "src/styles.css" },
    ],
  },
  { name: "package.json", type: "file", path: "package.json" },
  { name: "README.md", type: "file", path: "README.md" },
];

const TreeIcon: React.FC<TreeIconProps> = ({ item, isOpen }) => {
  if (item.icon) {
    const IconComponent = item.icon;
    return <IconComponent />;
  }
  if (item.type === "folder") {
    return <FolderIcon isOpen={isOpen} />;
  }
  if (item.name.endsWith(".js") || item.name.endsWith(".jsx"))
    return <JsIcon />;
  if (item.name.endsWith(".html")) return <HtmlIcon />;
  if (item.name.endsWith(".css")) return <CssIcon />;

  return <FileIcon />;
};

const TreeNode: React.FC<TreeNodeProps> = ({
  item,
  path = "",
}) => {
  const isFolder = item.type === "folder";
  const [isOpen, setIsOpen] = useState(isFolder);
  const { selectedFiles, toggleSelectedFile, addSelectedFile, removeSelectedFile } = useTutorialStore();
  
  const currentPath = item.path || (path ? `${path}/${item.name}` : item.name);
  const isSelected = selectedFiles.includes(currentPath);

  // Function to get all file paths within a folder recursively
  const getAllFilePaths = (item: FileTreeItem, basePath: string = ""): string[] => {
    const paths: string[] = [];
    
    if (item.type === "file") {
      paths.push(item.path);
    } else if (item.children) {
      item.children.forEach(child => {
        paths.push(...getAllFilePaths(child, item.path));
      });
    }
    
    return paths;
  };

  // Check if all files in folder are selected
  const areAllFilesSelected = (item: FileTreeItem): boolean => {
    if (item.type === "file") {
      return selectedFiles.includes(item.path);
    }
    
    if (!item.children) return true;
    
    const allFilePaths = getAllFilePaths(item);
    return allFilePaths.length > 0 && allFilePaths.every(filePath => selectedFiles.includes(filePath));
  };

  // Check if some (but not all) files in folder are selected
  const areSomeFilesSelected = (item: FileTreeItem): boolean => {
    if (item.type === "file") return false;
    
    if (!item.children) return false;
    
    const allFilePaths = getAllFilePaths(item);
    return allFilePaths.some(filePath => selectedFiles.includes(filePath)) && 
           !allFilePaths.every(filePath => selectedFiles.includes(filePath));
  };

  const isFolderFullySelected = isFolder && areAllFilesSelected(item);
  const isFolderPartiallySelected = isFolder && areSomeFilesSelected(item);

  // Use useEffect to manage indeterminate state properly
  const [checkboxRef, setCheckboxRef] = React.useState<HTMLInputElement | null>(null);
  
  React.useEffect(() => {
    if (checkboxRef && isFolder) {
      checkboxRef.indeterminate = isFolderPartiallySelected;
    }
  }, [checkboxRef, isFolder, isFolderPartiallySelected]);

  const handleToggle = () => {
    if (isFolder) {
      setIsOpen(!isOpen);
    }
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    
    if (isFolder) {
      const allFilePaths = getAllFilePaths(item);
      
      if (isFolderFullySelected) {
        // Unselect all files in folder
        allFilePaths.forEach(filePath => {
          if (selectedFiles.includes(filePath)) {
            removeSelectedFile(filePath);
          }
        });
      } else {
        // Select all files in folder
        allFilePaths.forEach(filePath => {
          if (!selectedFiles.includes(filePath)) {
            addSelectedFile(filePath);
          }
        });
      }
    } else {
      toggleSelectedFile(currentPath);
    }
    console.log("Selected files:", selectedFiles);
  };

  return (
    <div className="text-gray-700 dark:text-gray-300 relative">
      <div
        className={`flex items-center py-1.5 px-2 rounded-md cursor-pointer transition-all duration-150 border border-transparent hover:border-slate-500`}
        onClick={handleToggle}
      >
        <div className="flex items-center flex-grow">
          {isFolder ? (
            <ChevronIcon isOpen={isOpen} />
          ) : (
            <div className="w-4 shrink-0"></div>
          )}
          <div className="flex items-center ml-1">
            <TreeIcon item={item} isOpen={isOpen} />
            <span className="text-sm text-white ml-1.5">{item.name}</span>
          </div>
        </div>
        <input
          type="checkbox"
          checked={isFolder ? isFolderFullySelected : isSelected}
          ref={setCheckboxRef}
          onChange={handleCheckboxChange}
          onClick={(e) => e.stopPropagation()}
          className="ml-2 w-5 h-5 appearance-none bg-slate-800 border-2 border-gray-600 rounded-sm 
                     transition-all duration-200 ease-in-out cursor-pointer
                     hover:border-blue-400 hover:bg-gray-700
                     checked:bg-slate-300 checked:border-slate-400 checked:hover:bg-slate-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transform hover:scale-110 active:scale-95
                     relative
                     before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:bottom-0
                     before:flex before:items-center before:justify-center
                     before:w-1.5 before:h-2.5 before:border-r-2 before:border-b-2 before:m-auto
                     before:border-white before:transform before:rotate-45 before:scale-0
                     checked:before:scale-100 before:transition-transform before:duration-150
                     after:content-[''] after:absolute after:top-0 after:left-0 after:right-0 after:bottom-0
                     after:flex after:items-center after:justify-center
                     after:w-2.5 after:h-0.5 after:bg-white after:m-auto after:scale-0
                     indeterminate:after:scale-100 after:transition-transform after:duration-150
                     indeterminate:before:scale-0 indeterminate:bg-slate-400 indeterminate:border-slate-400"
        />
      </div>

      <div
        className={`pl-4 relative overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? "max-h-none opacity-100" : "max-h-0 opacity-0"}`}
      >
        <div className="absolute left-[13px] top-0 bottom-0 w-px bg-gray-800"></div>
        {isFolder &&
          isOpen &&
          item.children &&
          item.children.map((child: FileTreeItem) => (
            <TreeNode
              key={child.name}
              item={child}
              path={currentPath}
            />
          ))}
      </div>
    </div>
  );
};

export default function FileTree({ fileTreeData = defaultFileTreeData }: FileTreeProps) {
  const { selectedFiles, addSelectedFile, removeSelectedFile, clearSelectedFiles, includeFileTypes, excludeFileTypes } = useTutorialStore();
  const [isHydrated, setIsHydrated] = useState(false);

  // Ensure component is hydrated before showing dynamic content
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Parse include and exclude file types from store
  const parseFileTypes = (fileTypesString: string): string[] => {
    return fileTypesString
      .split(/,|\n/)
      .map(type => type.trim().replace(/"/g, ''))
      .filter(type => type.length > 0);
  };

  const includedExtensions = parseFileTypes(includeFileTypes);
  const excludedPatterns = parseFileTypes(excludeFileTypes);

  const specialIncludedFiles = [
    "Dockerfile", "Makefile", "requirements.txt", "package.json", "Cargo.toml", 
    "go.mod", "pom.xml"
  ];

  // Function to collect all file paths from file tree
  const collectAllFilePaths = (items: FileTreeItem[]): string[] => {
    const paths: string[] = [];
    
    const traverse = (items: FileTreeItem[]) => {
      items.forEach(item => {
        if (item.type === "file") {
          paths.push(item.path);
        } else if (item.children) {
          traverse(item.children);
        }
      });
    };
    
    traverse(items);
    return paths;
  };

  // Function to get all file paths from the tree data (for manual buttons)
  const getAllFilePaths = (items: FileTreeItem[]): string[] => {
    return collectAllFilePaths(items);
  };

  // Function to get filtered file paths (included and not excluded) - simplified for manual buttons
  const getFilteredFilePaths = (items: FileTreeItem[]): string[] => {
    const allPaths = collectAllFilePaths(items);
    return allPaths.filter((path: string) => {
      const fileName = path.split('/').pop() || '';
      const fileExtension = fileName.split('.').pop()?.toLowerCase() || '';
      
      // Check special files first
      if (specialIncludedFiles.includes(fileName)) {
        return true;
      }
      
      // Check if file matches included patterns
      return includedExtensions.some(pattern => {
        const cleanPattern = pattern.trim().toLowerCase().replace(/['"]/g, '');
        
        if (cleanPattern.startsWith('*.')) {
          const patternExt = cleanPattern.substring(2);
          return fileExtension === patternExt;
        } else if (cleanPattern.startsWith('.')) {
          const patternExt = cleanPattern.substring(1);
          return fileExtension === patternExt;
        } else if (cleanPattern === fileName.toLowerCase()) {
          return true;
        } else {
          return fileExtension === cleanPattern;
        }
      });
    });
  };

  const allFilePaths = getAllFilePaths(fileTreeData);
  const filteredFilePaths = getFilteredFilePaths(fileTreeData);
  const areAllFilesSelected = allFilePaths.length > 0 && allFilePaths.every((path: string) => selectedFiles.includes(path));
  const areAllFilteredFilesSelected = filteredFilePaths.length > 0 && filteredFilePaths.every((path: string) => selectedFiles.includes(path));

  const handleSelectAll = () => {
    if (areAllFilesSelected) {
      // Deselect all files
      clearSelectedFiles();
    } else {
      // Select all files
      allFilePaths.forEach((path: string) => {
        if (!selectedFiles.includes(path)) {
          addSelectedFile(path);
        }
      });
    }
  };

  const handleAutoSelect = () => {
    if (areAllFilteredFilesSelected) {
      // Deselect only the filtered files
      filteredFilePaths.forEach((path: string) => {
        if (selectedFiles.includes(path)) {
          removeSelectedFile(path);
        }
      });
    } else {
      // Select only the filtered files
      filteredFilePaths.forEach((path: string) => {
        if (!selectedFiles.includes(path)) {
          addSelectedFile(path);
        }
      });
    }
  };

  return (
    <div className="font-mono w-full p-4 mt-4 text-white bg-black rounded-lg border border-gray-800 flex flex-col max-h-[80vh]">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 flex-shrink-0">
        <h2 className="text-lg font-semibold">Repository File Tree</h2>
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm">
          <div className="flex items-center gap-2">
            <Box className="inline-block text-slate-500" />
            <p>Selected File Sizes:</p>
            <span className="font-semibold">
              {selectedFiles.length}
            </span>
            <span>(10MB)</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleAutoSelect}
              className="px-3 py-1 text-xs bg-blue-700 hover:bg-blue-600 border border-blue-600 rounded-md transition-colors duration-150"
              title="Select/deselect files based on included extensions and exclude patterns"
            >
              {areAllFilteredFilesSelected ? 'Deselect Code Files' : 'Auto Select Code Files'}
            </button>
            <button
              onClick={handleSelectAll}
              className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-md transition-colors duration-150"
            >
              {areAllFilesSelected ? 'Deselect All' : 'Select All'}
            </button>
          </div>
        </div>
      </div>
      <div className="text-xs text-gray-400 mb-3 flex-shrink-0">
        <p className="mb-1">
          <span className="font-semibold text-green-400">Auto-Select Filters:</span> 
          {isHydrated ? ` ${filteredFilePaths.length} of ${allFilePaths.length} files match code patterns` : ' Loading file patterns...'}
        </p>
        <details className="cursor-pointer">
          <summary className="hover:text-gray-300">View filter details</summary>
          <div className="mt-2 p-2 bg-gray-900 rounded text-xs max-h-32 overflow-y-auto">
            <div className="mb-2">
              <p className="text-green-300 font-semibold mb-1">Included patterns:</p>
              <p className="text-green-200 text-xs leading-relaxed">
                {includedExtensions.length > 0 ? includedExtensions.join(', ') : 'No patterns defined'}
              </p>
            </div>
            <div>
              <p className="text-red-300 font-semibold mb-1">Excluded patterns:</p>
              <p className="text-red-200 text-xs leading-relaxed">
                {excludedPatterns.length > 0 ? excludedPatterns.join(', ') : 'No patterns defined'}
              </p>
            </div>
          </div>
        </details>
      </div>
      <div className="w-full text-white overflow-y-auto flex-1 min-h-0 pr-2">
        <div className="space-y-1">
          {fileTreeData.map((item) => (
            <TreeNode
              key={item.name}
              item={item}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
