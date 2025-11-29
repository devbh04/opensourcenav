import faiss
import os
import pickle
import numpy as np
from typing import List, Dict, Any
from app.utils.config import GEMINI_API_KEY
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class EnhancedGeminiEmbedder:
    def __init__(self):
        # Use latest Gemini embedding model with task optimization
        self.doc_embedder = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",  # Latest Gemini model
            google_api_key=GEMINI_API_KEY,
            task_type="retrieval_document"  # Optimized for document retrieval
        )
        
        # Separate embedder for queries (optimized for search)
        self.query_embedder = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=GEMINI_API_KEY,
            task_type="retrieval_query"  # Optimized for query processing
        )
        
        print("✅ Enhanced Gemini embedder initialized with task-optimized models")

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = file_path.lower().split('.')[-1]
        language_map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript',
            'jsx': 'react', 'tsx': 'react', 'java': 'java',
            'cpp': 'cpp', 'c': 'c', 'go': 'go', 'rs': 'rust',
            'php': 'php', 'rb': 'ruby', 'md': 'markdown',
            'yml': 'yaml', 'yaml': 'yaml', 'json': 'json',
            'html': 'html', 'css': 'css', 'scss': 'scss',
            'vue': 'vue', 'svelte': 'svelte', 'sql': 'sql'
        }
        return language_map.get(ext, 'unknown')

    def _create_enhanced_metadata(self, chunk: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create rich metadata for each chunk"""
        content = chunk.get('content', '')
        file_path = chunk.get('original_file', chunk.get('file', ''))
        file_type = chunk.get('file_type', 'unknown')
        importance = chunk.get('importance', 5)
        
        # Enhanced metadata
        metadata = {
            'chunk_id': index,
            'file_path': file_path,
            'file_type': file_type,
            'language': self._detect_language(file_path),
            'importance': importance,
            'content_length': len(content),
            'has_functions': any(pattern in content for pattern in ['def ', 'function ', 'const ', 'let ', 'var ']),
            'has_classes': any(pattern in content for pattern in ['class ', 'interface ', 'struct ']),
            'is_config': any(term in file_path.lower() for term in ['config', 'settings', '.env', 'dockerfile']),
            'is_test': any(term in file_path.lower() for term in ['test', 'spec', '__test__']),
            'is_main': any(term in file_path.lower() for term in ['main', 'index', 'app']),
            'is_api': any(term in file_path.lower() for term in ['api', 'route', 'endpoint', 'controller']),
            'is_component': any(term in file_path.lower() for term in ['component', 'widget', 'view']),
            'complexity_score': self._calculate_complexity(content),
            'keywords': self._extract_keywords(content)
        }
        
        return metadata

    def _calculate_complexity(self, content: str) -> float:
        """Calculate rough complexity score for content"""
        complexity = 0
        complexity += content.count('if ') * 1
        complexity += content.count('for ') * 1.5
        complexity += content.count('while ') * 1.5
        complexity += content.count('try ') * 2
        complexity += content.count('class ') * 3
        complexity += content.count('def ') * 2
        complexity += content.count('async ') * 1.5
        return min(complexity / 10.0, 10.0)  # Normalize to 0-10 scale

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from content"""
        # Common important programming keywords
        important_keywords = []
        
        # Framework/library detection
        frameworks = ['react', 'vue', 'angular', 'express', 'fastapi', 'django', 'flask', 'spring']
        for fw in frameworks:
            if fw in content.lower():
                important_keywords.append(fw)
        
        # Database keywords
        db_terms = ['database', 'sql', 'mongodb', 'postgres', 'mysql', 'sqlite']
        for term in db_terms:
            if term in content.lower():
                important_keywords.append(term)
        
        # Architecture patterns
        patterns = ['api', 'rest', 'graphql', 'microservice', 'middleware', 'authentication', 'authorization']
        for pattern in patterns:
            if pattern in content.lower():
                important_keywords.append(pattern)
        
        return important_keywords[:10]  # Limit to top 10

def embed_chunks(chunks: list):
    """Enhanced chunk embedding with better context and metadata"""
    print("[INFO] Creating enhanced embeddings with improved context...")
    
    embedder = EnhancedGeminiEmbedder()
    enhanced_texts = []
    metadata_list = []
    
    for i, chunk in enumerate(chunks):
        content = chunk.get('content', '')
        file_path = chunk.get('original_file', chunk.get('file', ''))
        file_type = chunk.get('file_type', 'unknown')
        importance = chunk.get('importance', 5)
        
        # Create enhanced metadata
        metadata = embedder._create_enhanced_metadata(chunk, i)
        metadata_list.append(metadata)
        
        # Create rich contextual representation
        context_parts = [
            f"FILE: {file_path}",
            f"TYPE: {file_type}",
            f"LANGUAGE: {metadata['language']}",
            f"IMPORTANCE: {importance}/10"
        ]
        
        # Add structural context
        if metadata['has_functions']:
            context_parts.append("CONTAINS: functions")
        if metadata['has_classes']:
            context_parts.append("CONTAINS: classes")
        if metadata['is_config']:
            context_parts.append("CATEGORY: configuration")
        if metadata['is_test']:
            context_parts.append("CATEGORY: test")
        if metadata['is_api']:
            context_parts.append("CATEGORY: api")
        if metadata['is_component']:
            context_parts.append("CATEGORY: component")
        
        # Add keywords
        if metadata['keywords']:
            context_parts.append(f"KEYWORDS: {', '.join(metadata['keywords'])}")
        
        # Create enhanced text for embedding
        context_header = " | ".join(context_parts)
        enhanced_text = f"{context_header}\n\n{content}"
        enhanced_texts.append(enhanced_text)
        
        if i % 100 == 0:
            print(f"[INFO] Processed {i+1}/{len(chunks)} chunks")
    
    try:
        # Create embeddings in batches for efficiency
        batch_size = 50
        all_embeddings = []
        
        for i in range(0, len(enhanced_texts), batch_size):
            batch = enhanced_texts[i:i + batch_size]
            batch_embeddings = embedder.doc_embedder.embed_documents(batch)
            all_embeddings.extend(batch_embeddings)
            print(f"[INFO] Embedded batch {i//batch_size + 1}/{(len(enhanced_texts)-1)//batch_size + 1}")
        
        # Convert to numpy array
        np_vectors = np.array(all_embeddings, dtype='float32')
        dimension = np_vectors.shape[1]
        
        # Create optimized FAISS index - Use HNSW for better search quality
        print(f"[INFO] Creating optimized FAISS index with {dimension}D vectors...")
        
        # For better search quality, use HNSW instead of flat index
        if len(chunks) > 1000:
            # For larger datasets, use IVF + HNSW
            nlist = min(256, int(np.sqrt(len(chunks))))
            quantizer = faiss.IndexHNSWFlat(dimension, 32)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            index.train(np_vectors)
            index.nprobe = min(32, nlist // 4)
            print(f"✅ Using IVF-HNSW index: {nlist} clusters")
        else:
            # For smaller datasets, use high-quality HNSW
            index = faiss.IndexHNSWFlat(dimension, 64)  # M=64 for high quality
            index.hnsw.efConstruction = 400  # High quality construction
            index.hnsw.efSearch = 128  # High quality search
            print("✅ Using high-quality HNSW index")
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(np_vectors)
        index.add(np_vectors)

        # Save enhanced index and metadata
        faiss.write_index(index, "vector.index")
        
        # Save enhanced document map with metadata
        enhanced_doc_map = {
            'chunks': chunks,
            'metadata': metadata_list,
            'dimension': dimension,
            'index_type': 'HNSW' if len(chunks) <= 1000 else 'IVF-HNSW',
            'total_chunks': len(chunks),
            'embedding_model': 'text-embedding-004',
            'enhancement_version': '2.0'
        }
        
        with open("doc_map.pkl", "wb") as f:
            pickle.dump(enhanced_doc_map, f)
        
        print(f"✅ Enhanced FAISS index created: {len(chunks)} chunks, {dimension}D embeddings")
        print(f"✅ Rich metadata saved for {len(metadata_list)} chunks")
        
    except Exception as e:
        print(f"❌ Error creating enhanced embeddings: {e}")
        raise

# Create global enhanced embedder instance
_enhanced_embedder = None

def get_enhanced_embedder():
    """Get or create enhanced embedder instance"""
    global _enhanced_embedder
    if _enhanced_embedder is None:
        _enhanced_embedder = EnhancedGeminiEmbedder()
    return _enhanced_embedder

def embed_query(query: str) -> np.ndarray:
    """Enhanced query embedding with context optimization"""
    embedder = get_enhanced_embedder()
    try:
        # Use query-optimized embedder
        embedding = embedder.query_embedder.embed_query(query)
        
        # Convert to numpy and normalize
        embedding_array = np.array([embedding], dtype='float32')
        faiss.normalize_L2(embedding_array)
        
        return embedding_array
        
    except Exception as e:
        print(f"❌ Error embedding query: {e}")
        raise