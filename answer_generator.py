import json
from sentence_transformers import SentenceTransformer, util
import openai
import os

openai.api_base = "https://aipipe.org/openai/v1"
openai.api_key = os.getenv("AIPIPE_TOKEN")  # or paste directly for now

model = SentenceTransformer("all-MiniLM-L6-v2")
doc_embeddings = None
documents = []
sources = []

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
    global doc_embeddings
    if doc_embeddings is None:
        load_data()
        doc_embeddings = model.encode(documents, convert_to_tensor=True)

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

def generate_answer(question):
    context, refs = find_top_k_contexts(question)
    context_text = "\n\n".join(context)
    prompt = f"""You are a virtual TA. A student asked:

Question: {question}

Relevant context:
{context_text}

Give a helpful answer and cite forum links if relevant.
Answer:"""

    response = openai.ChatCompletion.create(
        model="openai/gpt-3.5-turbo",
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
