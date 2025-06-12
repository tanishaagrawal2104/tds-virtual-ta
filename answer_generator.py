import json
from sentence_transformers import SentenceTransformer, util
import openai
import torch

openai.api_base = "https://aipipe.org/openai/v1"
openai.api_key = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDE4OTdAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.0K_02nynzpAb1c66nTBI6Rt8CMLWBpi8gLrYam3qvAU"  # <- paste your actual token here

MODEL_NAME = "openai/gpt-3.5-turbo"

model = SentenceTransformer("all-MiniLM-L6-v2")

# Load course + discourse data
with open("data/course.json", encoding="utf-8") as f:
    course_data = json.load(f)

with open("data/discourse.json", encoding="utf-8") as f:
    forum_data = json.load(f)

# Combine everything into a corpus
documents = []
sources = []

for item in course_data:
    documents.append(item["content"])
    sources.append({"type": "course", "section": item["section"]})

for post in forum_data:
    documents.append(post["content"])
    sources.append({
        "type": "forum",
        "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{post['topic_id']}",
        "author": post["author"],
        "created_at": post["created_at"]
    })

doc_embeddings = None  # lazy load only when needed

def load_embeddings():
    global doc_embeddings
    if doc_embeddings is None:
        print("Loading embeddings...")
        doc_embeddings = model.encode(documents, convert_to_tensor=True)

# Find relevant context
def find_top_k_contexts(query, k=5):
    load_embeddings()
    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, doc_embeddings, top_k=k)[0]
    context = []
    refs = []
    for hit in hits:
        idx = hit["corpus_id"]
        context.append(documents[idx])
        refs.append(sources[idx])
    return context, refs

# Ask the LLM
def generate_answer(question):
    context, refs = find_top_k_contexts(question)

    context_text = "\n\n".join(context)
    prompt = f"""You are a virtual TA. A student asked:

Question: {question}

Relevant context from the course and forum:
{context_text}

Give a helpful answer and cite 1-2 matching forum links if relevant.
Answer:"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # This works via AIPipe
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    answer = response['choices'][0]['message']['content']
    
    links = []
    for ref in refs:
        if ref["type"] == "forum":
            links.append({
                "url": ref["url"],
                "text": f"Post by {ref['author']} on {ref['created_at'][:10]}"
            })

    return {
        "answer": answer.strip(),
        "links": links[:2]
    }

# For CLI test
if __name__ == "__main__":
    q = input("Ask a TDS question: ")
    response = generate_answer(q)
    print("\nAnswer:", response["answer"])
    print("\nLinks:")
    for link in response["links"]:
        print(f"- {link['text']}: {link['url']}")
