#!/usr/bin/env python3
"""
Blog Generator Script
=====================
Generates HTML blog posts from Markdown files.

Usage:
    python generate_blog.py

This script will:
1. Read all .md files from the blog/posts/ directory
2. Convert them to HTML using the template
3. Generate individual article pages in blog/articles/
4. Update the blog.html listing page

Markdown file format:
---------------------
Each markdown file should start with YAML frontmatter:

---
title: Your Post Title
date: 2026-02-24
tags: [Azure, Cloud, Tutorial]
excerpt: A brief description of the post for the listing page.
image: optional-cover-image.jpg
---

Your markdown content here...

"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Try to import required packages, install if missing
try:
    import markdown
except ImportError:
    print("Installing markdown package...")
    os.system(f"{sys.executable} -m pip install markdown")
    import markdown

try:
    import yaml
except ImportError:
    print("Installing PyYAML package...")
    os.system(f"{sys.executable} -m pip install pyyaml")
    import yaml

try:
    from mdx_linkify.mdx_linkify import LinkifyExtension
    HAS_LINKIFY = True
except ImportError:
    print("Installing linkify-it-py and mdx_linkify packages...")
    os.system(f"{sys.executable} -m pip install linkify-it-py mdx_linkify")
    try:
        from mdx_linkify.mdx_linkify import LinkifyExtension
        HAS_LINKIFY = True
    except ImportError:
        HAS_LINKIFY = False
        print("Warning: Could not load linkify extension. Bare URLs won't be auto-linked.")


# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
POSTS_DIR = ROOT_DIR / "blog" / "posts"
ARTICLES_DIR = ROOT_DIR / "blog" / "articles"
TEMPLATE_PATH = ROOT_DIR / "blog" / "template.html"
BLOG_HTML_PATH = ROOT_DIR / "blog.html"


def ensure_directories():
    """Create necessary directories if they don't exist."""
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def read_template():
    """Read the HTML template file."""
    if not TEMPLATE_PATH.exists():
        print(f"Error: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def parse_markdown_file(filepath):
    """Parse a markdown file and extract frontmatter and content."""
    content = filepath.read_text(encoding="utf-8")
    
    # Extract YAML frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    
    if not frontmatter_match:
        print(f"Warning: No frontmatter found in {filepath.name}")
        return None
    
    try:
        frontmatter = yaml.safe_load(frontmatter_match.group(1))
    except yaml.YAMLError as e:
        print(f"Error parsing frontmatter in {filepath.name}: {e}")
        return None
    
    # Get markdown content after frontmatter
    md_content = content[frontmatter_match.end():]
    
    # Convert markdown to HTML with extensions
    extensions = ['fenced_code', 'tables', 'toc', 'nl2br']
    if HAS_LINKIFY:
        extensions.append(LinkifyExtension())
    
    md = markdown.Markdown(extensions=extensions)
    html_content = md.convert(md_content)
    
    # Calculate reading time (roughly 200 words per minute)
    word_count = len(md_content.split())
    reading_time = max(1, round(word_count / 200))
    
    # Parse date
    date = frontmatter.get('date')
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, datetime):
        pass
    else:
        date = datetime.now()
    
    return {
        'title': frontmatter.get('title', 'Untitled'),
        'date': date,
        'date_formatted': date.strftime('%B %d, %Y'),
        'tags': frontmatter.get('tags', []),
        'excerpt': frontmatter.get('excerpt', ''),
        'image': frontmatter.get('image', ''),
        'content': html_content,
        'reading_time': reading_time,
        'slug': filepath.stem,
        'filepath': filepath
    }


def generate_tags_html(tags):
    """Generate HTML for tags."""
    return '\n'.join([f'<span class="article-tag">{tag}</span>' for tag in tags])


def generate_article_html(post, template, all_posts):
    """Generate HTML for a single article page."""
    # Find previous and next posts
    sorted_posts = sorted(all_posts, key=lambda x: x['date'], reverse=True)
    current_idx = next((i for i, p in enumerate(sorted_posts) if p['slug'] == post['slug']), -1)
    
    prev_html = ""
    next_html = ""
    
    if current_idx < len(sorted_posts) - 1:
        prev_post = sorted_posts[current_idx + 1]
        prev_html = f'''<a href="{prev_post['slug']}.html" class="article-nav-link">
            ← Previous
            <span>{prev_post['title']}</span>
        </a>'''
    
    if current_idx > 0:
        next_post = sorted_posts[current_idx - 1]
        next_html = f'''<a href="{next_post['slug']}.html" class="article-nav-link" style="text-align: right; margin-left: auto;">
            Next →
            <span>{next_post['title']}</span>
        </a>'''
    
    # Replace template placeholders
    html = template
    html = html.replace('{{title}}', post['title'])
    html = html.replace('{{date}}', post['date_formatted'])
    html = html.replace('{{reading_time}}', str(post['reading_time']))
    html = html.replace('{{tags_html}}', generate_tags_html(post['tags']))
    html = html.replace('{{excerpt}}', post['excerpt'])
    html = html.replace('{{content}}', post['content'])
    html = html.replace('{{prev_post}}', prev_html)
    html = html.replace('{{next_post}}', next_html)
    
    # Header image
    header_image_html = ""
    if post['image']:
        header_image_html = f'<div class="article-header-image"><img src="../../blog/images/{post["image"]}" alt="{post["title"]}"></div>'
    html = html.replace('{{header_image}}', header_image_html)
    
    return html


def generate_blog_card(post):
    """Generate HTML for a blog card in the listing page."""
    tags_html = ""
    if post['tags']:
        tags_html = f'<span class="blog-card-tag">{post["tags"][0]}</span>'
    
    image_html = '''<div class="blog-card-image-placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <line x1="10" y1="9" x2="8" y2="9"></line>
        </svg>
    </div>'''
    
    if post['image']:
        image_html = f'<img src="blog/images/{post["image"]}" alt="{post["title"]}" class="blog-card-image">'
    
    return f'''<article class="blog-card">
    {image_html}
    <div class="blog-card-content">
        <div class="blog-card-meta">
            <span class="blog-card-date">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                {post['date_formatted']}
            </span>
            {tags_html}
        </div>
        <h2 class="blog-card-title">
            <a href="blog/articles/{post['slug']}.html">{post['title']}</a>
        </h2>
        <p class="blog-card-excerpt">{post['excerpt']}</p>
        <a href="blog/articles/{post['slug']}.html" class="blog-card-link">
            Read more
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </a>
    </div>
</article>'''


def update_blog_listing(posts):
    """Update the blog.html listing page with all posts."""
    if not BLOG_HTML_PATH.exists():
        print(f"Error: blog.html not found at {BLOG_HTML_PATH}")
        return
    
    # Sort posts by date (newest first)
    sorted_posts = sorted(posts, key=lambda x: x['date'], reverse=True)
    
    # Generate cards HTML
    if sorted_posts:
        cards_html = '\n'.join([generate_blog_card(post) for post in sorted_posts])
    else:
        cards_html = '<p class="no-posts">No posts yet. Check back soon!</p>'
    
    # Read current blog.html
    blog_html = BLOG_HTML_PATH.read_text(encoding="utf-8")
    
    # Replace the blog-posts content
    pattern = r'(<div class="blog-posts" id="blog-posts">).*?(</div>\s*</div>\s*</main>)'
    replacement = f'\\1\n{cards_html}\n            \\2'
    new_html = re.sub(pattern, replacement, blog_html, flags=re.DOTALL)
    
    # Write updated blog.html
    BLOG_HTML_PATH.write_text(new_html, encoding="utf-8")
    print(f"Updated: {BLOG_HTML_PATH}")


def main():
    """Main function to generate the blog."""
    print("=" * 50)
    print("Blog Generator")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories()
    
    # Read template
    template = read_template()
    
    # Find all markdown files
    md_files = list(POSTS_DIR.glob("*.md"))
    
    if not md_files:
        print(f"\nNo markdown files found in {POSTS_DIR}")
        print("Create a .md file with frontmatter to get started.")
        # Still update blog.html to show "no posts" message
        update_blog_listing([])
        return
    
    print(f"\nFound {len(md_files)} markdown file(s)")
    
    # Parse all posts
    posts = []
    for md_file in md_files:
        print(f"Processing: {md_file.name}")
        post = parse_markdown_file(md_file)
        if post:
            posts.append(post)
    
    if not posts:
        print("No valid posts found.")
        update_blog_listing([])
        return
    
    # Generate article pages
    print(f"\nGenerating {len(posts)} article page(s)...")
    for post in posts:
        article_html = generate_article_html(post, template, posts)
        output_path = ARTICLES_DIR / f"{post['slug']}.html"
        output_path.write_text(article_html, encoding="utf-8")
        print(f"  Created: {output_path.name}")
    
    # Update blog listing
    print("\nUpdating blog listing...")
    update_blog_listing(posts)
    
    print("\n" + "=" * 50)
    print("Blog generation complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
