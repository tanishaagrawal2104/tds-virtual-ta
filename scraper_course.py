from bs4 import BeautifulSoup
import json
import os

def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    content = []
    current_section = None

    for tag in soup.find_all(["h1", "h2", "h3", "details", "p", "li", "table"]):
        if tag.name == "details":
            summary = tag.find("summary")
            section_title = summary.text.strip() if summary else "Details"
            details_content = "\n".join([p.text.strip() for p in tag.find_all("p")])
            content.append({"section": section_title, "content": details_content})

        elif tag.name in ["h1", "h2", "h3"]:
            current_section = {"section": tag.text.strip(), "content": ""}
            content.append(current_section)

        elif tag.name == "table":
            rows = []
            for row in tag.find_all("tr"):
                cells = [cell.text.strip() for cell in row.find_all(["th", "td"])]
                rows.append(" | ".join(cells))
            if current_section:
                current_section["content"] += "\n" + "\n".join(rows)

        else:
            if current_section:
                current_section["content"] += "\n" + tag.text.strip()

    return content

def scrape_all_html():
    html_dir = os.path.join("data", "html")
    all_content = []

    for filename in os.listdir(html_dir):
        if filename.endswith(".html"):
            file_path = os.path.join(html_dir, filename)
            print(f"Processing {filename}")
            content = extract_text_from_html(file_path)
            all_content.extend(content)

    output_file = os.path.join("data", "course.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_content, f, indent=2, ensure_ascii=False)

    print(f"Combined course.json generated with {len(all_content)} sections.")

if __name__ == "__main__":
    scrape_all_html()
