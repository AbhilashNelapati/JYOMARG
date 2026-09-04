import re

# Stop words to filter out common English words safely without heavy NLTK pipelines
STOP_WORDS = {
    "and", "the", "with", "for", "from", "that", "this", "can", "will", "are", 
    "is", "was", "were", "have", "has", "had", "not", "but", "you", "they", 
    "their", "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "experience", "years", "working", "knowledge", "skills", "ability", "role",
    "team", "work", "strong", "good", "excellent", "required", "preferred", "using",
    "must", "should", "could", "would", "about", "into", "through", "during", "before",
    "requirements", "responsibilities", "job", "candidate", "build", "develop", "looking"
}

def extract_keywords(text: str) -> set:
    """
    Extracts potential skill keywords from clean text using simple NLP rules.
    Returns a set of unique keywords to optimize matching speed.
    """
    # Split text into tokens (words)
    tokens = text.split()
    
    keywords = set()
    for token in tokens:
        # Require minimum length to be considered a skill (except edge cases like 'c', 'r', 'go')
        if len(token) > 2 or token in ["c", "r", "go", "c#"]:
            # Drop purely numeric tokens like "2023"
            if not token.isnumeric():
                if token not in STOP_WORDS:
                    keywords.add(token)
                    
    return keywords
