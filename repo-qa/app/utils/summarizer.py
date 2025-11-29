import os
import time
from typing import List, Dict
from app.utils.config import GEMINI_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI
from transformers import GPT2TokenizerFast
from app.utils.llm_tracker import tracked_llm_call, tracker

llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", google_api_key=GEMINI_API_KEY)
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

MAX_CHUNK_TOKENS = 6000
MAX_FINAL_TOKENS = 10000

chunk_summary_prompt = "Generate a concise, documentation-style summary of the following code file(s):\n\n{code}\n\nFocus on:\n- Main purpose and functionality\n- Key components/classes/functions\n- Important dependencies or integrations\n- Notable features or patterns"
project_summary_prompt = "Create a comprehensive README.md for this software project based on the following module summaries:\n\n{summaries}\n\nStructure the README with these sections:\n1. **Project Title & Description**\n2. **Features**\n3. **Architecture & Structure**\n4. **Installation & Setup**\n5. **Usage**\n6. **Configuration**\n7. **Contributing**"

def count_tokens(text: str) -> int: return len(tokenizer.encode(text))
def extract_text(response): return response.content if hasattr(response, "content") else str(response)

def chunk_summaries_by_tokens(summaries: List[str], max_tokens: int) -> List[str]:
    chunks, current_chunk, current_tokens = [], [], 0
    for summary in summaries:
        summary_tokens = count_tokens(summary)
        if current_tokens + summary_tokens <= max_tokens:
            current_chunk.append(summary); current_tokens += summary_tokens
        else:
            if current_chunk: chunks.append("\n\n".join(current_chunk))
            current_chunk, current_tokens = [summary], summary_tokens
    if current_chunk: chunks.append("\n\n".join(current_chunk))
    return chunks

def generate_hierarchical_summary(summary_chunks: List[str]) -> str:
    if len(summary_chunks) == 1: return summary_chunks[0]
    print(f"[INFO] Generating hierarchical summary from {len(summary_chunks)} chunks...")
    condensed_summaries = []
    for i, chunk in enumerate(summary_chunks):
        print(f"[INFO] Condensing summary chunk {i+1}/{len(summary_chunks)}")
        condense_prompt = f"Condense the following module summaries into a more concise overview:\n\n{chunk}"
        
        # Enhanced tracking for hierarchical summarization
        response = tracked_llm_call(
            module="summarizer",
            function="generate_hierarchical_summary",
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=condense_prompt
        )
        
        condensed_summaries.append(extract_text(response))
        if (i + 1) % 10 == 0: 
            print(f"[RATE LIMIT] Pausing 60s after {i+1} hierarchical summaries...")
            time.sleep(60)
    return "\n\n".join(condensed_summaries)

def generate_readme(chunks: List[Dict]) -> str:
    print(f"[INFO] Starting README generation for {len(chunks)} chunks...")
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"[INFO] Summarizing chunk {i + 1}/{len(chunks)} ({chunk['file']})")
        prompt = chunk_summary_prompt.format(code=f"File: {chunk['file']}\n\n{chunk['content']}")
        
        # Enhanced tracking for individual chunk summarization
        response = tracked_llm_call(
            module="summarizer",
            function="generate_readme_chunk",
            model="models/gemini-2.0-flash",
            llm_instance=llm,
            prompt=prompt
        )
        
        summaries.append(f"## {chunk['file']}\n{extract_text(response)}")
        if (i + 1) % 10 == 0: 
            print(f"[RATE LIMIT] Pausing 60s after {i+1} chunk summaries...")
            time.sleep(60)

    total_summary_tokens = sum(count_tokens(s) for s in summaries)
    if total_summary_tokens > MAX_FINAL_TOKENS:
        summary_chunks = chunk_summaries_by_tokens(summaries, MAX_CHUNK_TOKENS)
        final_summary = generate_hierarchical_summary(summary_chunks)
    else:
        final_summary = "\n\n".join(summaries)
    
    print("[INFO] Generating final README...")
    final_prompt = project_summary_prompt.format(summaries=final_summary)
    
    # Enhanced tracking for final README generation
    readme_response = tracked_llm_call(
        module="summarizer",
        function="generate_readme_final",
        model="models/gemini-2.0-flash",
        llm_instance=llm,
        prompt=final_prompt
    )
    
    # Export metrics after README generation
    tracker.export_metrics("readme_generation_metrics.json")
    
    return extract_text(readme_response)