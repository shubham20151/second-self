import argparse
import sys
from typing import List, Dict, Any
from lib.embeddings import embed_text, load_embeddings, cosine_similarity
from lib.storage import read_wiki_notes
from lib.llm import synthesize_answer
from lib.models import AskResult

def ask(question: str, top_k: int = 5) -> AskResult:
    print(f"Embedding question: '{question}'...")
    query_emb = embed_text(question)
    
    embeddings_dict = load_embeddings()
    if not embeddings_dict:
        print("No embeddings found. Run 'python pipeline.py process' first.")
        return AskResult(answer="I don't have any notes indexed yet.", sources=[])
        
    print("Searching for relevant notes...")
    # Calculate similarities
    scores = []
    for note_id, note_emb in embeddings_dict.items():
        sim = cosine_similarity(query_emb, note_emb)
        scores.append((note_id, sim))
        
    # Sort by similarity descending
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Take top K with a minimum relevance threshold
    top_results = [s for s in scores[:top_k] if s[1] > 0.15]
    
    if not top_results:
        return AskResult(answer="I don't have notes about that.", sources=[])
        
    # Load the matching notes
    all_notes = {n.id: n for n in read_wiki_notes()}
    
    sources = []
    retrieved_notes_text = ""
    
    for note_id, score in top_results:
        if note_id in all_notes:
            note = all_notes[note_id]
            sources.append({
                "id": note.id,
                "summary": note.summary,
                "relevance_score": score,
                "para": note.para
            })
            
            # Add to context string, truncating body if it's extremely long
            body_preview = note.body[:1500] 
            retrieved_notes_text += f"--- Note [{note.id}] ---\nSummary: {note.summary}\nContent: {body_preview}\n\n"
            
    print(f"Found {len(sources)} relevant notes. Synthesizing answer...")
    
    # Build context and prompt LLM
    answer = synthesize_answer(context=retrieved_notes_text, question=question)
    
    return AskResult(answer=answer, sources=sources)

def main():
    parser = argparse.ArgumentParser(description="Ask questions about your SecondSelf knowledge base.")
    parser.add_argument("question", type=str, help="The question you want to ask")
    args = parser.parse_args()
    
    result = ask(args.question)
    
    print("\n" + "="*50)
    print("SECONDSELF SAYS:")
    print("="*50)
    print(result.answer)
    print("-" * 50)
    if result.sources:
        print("Sources:")
        for s in result.sources:
            print(f"- [{s['id']}] {s['summary']} (Match: {s['relevance_score']:.2f})")
    else:
        print("No sources found.")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
