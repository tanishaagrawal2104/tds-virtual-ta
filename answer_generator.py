import json
import os
import openai
import numpy as np

# 🔐 AIPipe setup
openai.api_key = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDE4OTdAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.0K_02nynzpAb1c66nTBI6Rt8CMLWBpi8gLrYam3qvAU"  # You can also paste token directly for testing
openai.api_base = "https://aipipe.org/openai/v1"

documents = []
sources = []
embeddings = []

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_data():
    global documents, sources
    if documents:
        return  # already loaded

    with open("data/course.json", encoding="utf-8") as f:
        course_data = json.load(f)
    with open("data/discourse.json", encoding="utf-8") as f:
        forum_data = json.load(f)

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

def load_embeddings():
    global embeddings
    if embeddings:
        return

    load_data()
    print("🔁 Generating embeddings via AIPipe...")

    for doc in documents:
        try:
            res = openai.Embedding.create(
                model="text-embedding-3-small",
                input=doc
            )
            emb = np.array(res["data"][0]["embedding"])
            embeddings.append(emb)
        except Exception as e:
            print("⚠️ Embedding error:", e)
            embeddings.append(np.zeros(512))  # fallback

def find_top_k_contexts(query, k=5):
    load_embeddings()
    query_embedding = openai.Embedding.create(
        model="text-embedding-3-small",
        input=query
    )["data"][0]["embedding"]
    query_embedding = np.array(query_embedding)

    scored = []
    for i, emb in enumerate(embeddings):
        sim = cosine_similarity(query_embedding, emb)
        scored.append((sim, i))

    top_hits = sorted(scored, reverse=True)[:k]

    contexts = [documents[i] for _, i in top_hits]
    refs = [sources[i] for _, i in top_hits]
    return contexts, refs

def generate_answer(question):
    context, refs = find_top_k_contexts(question)
    context_text = "\n\n".join(context)

    prompt = f"""You are a helpful virtual TA. A student asked:

Question: {question}

Relevant information:
{context_text}

Give a clear and helpful answer. Include forum links if available.
Answer:"""

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    answer = res["choices"][0]["message"]["content"]

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
