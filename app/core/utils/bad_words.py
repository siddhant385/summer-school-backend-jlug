from better_profanity import profanity
from typing import List, Optional
from app.core.config import settings

# Initialize profanity filter with config-based custom words
def _initialize_profanity_filter():
    """Initialize the profanity filter with custom words from config"""
    profanity.load_censor_words()
    
    # Only add custom bad words if they exist and content moderation is enabled
    if (settings.ENABLE_CONTENT_MODERATION and 
        settings.bad_words_list and 
        len(settings.bad_words_list) > 0):
        profanity.add_censor_words(settings.bad_words_list)

# Initialize on module import
_initialize_profanity_filter()

def is_clean(text: str) -> bool:
    """
    Returns True if text does NOT contain profanity (English + Hindi).
    Used for validating review content before saving.
    """
    if not settings.ENABLE_CONTENT_MODERATION:
        return True
        
    if not text or not isinstance(text, str):
        return True
    
    # Check for profanity in the text
    return not profanity.contains_profanity(text.lower())

def censor_text(text: str) -> str:
    """
    Returns censored version of text if needed.
    Replaces bad words with asterisks.
    """
    if not settings.ENABLE_CONTENT_MODERATION:
        return text
        
    if not text or not isinstance(text, str):
        return text
    
    return profanity.censor(text)

def get_violation_words(text: str) -> List[str]:
    """
    Returns list of bad words found in the text.
    Useful for detailed error messages in reviews.
    """
    if not settings.ENABLE_CONTENT_MODERATION:
        return []
        
    if not text or not isinstance(text, str):
        return []
    
    violations = []
    text_lower = text.lower()
    
    # Only check against custom words if they exist
    if settings.bad_words_list and len(settings.bad_words_list) > 0:
        for word in settings.bad_words_list:
            if word in text_lower:
                violations.append(word)
    
    return violations

def validate_review_content(text: str, max_length: Optional[int] = None) -> dict:
    """
    Comprehensive validation for review content.
    Returns validation result with details.
    """
    # Use config value if max_length not provided
    if max_length is None:
        max_length = settings.MAX_REVIEW_LENGTH
    
    result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "cleaned_text": text
    }
    
    if not text or not isinstance(text, str):
        result["is_valid"] = False
        result["errors"].append("Review content cannot be empty")
        return result
    
    # Length check
    if len(text) > max_length:
        result["is_valid"] = False
        result["errors"].append(f"Review content exceeds maximum length of {max_length} characters")
    
    # Profanity check (only if content moderation is enabled)
    if settings.ENABLE_CONTENT_MODERATION and not is_clean(text):
        result["is_valid"] = False
        result["errors"].append("Review content contains inappropriate language")
        violations = get_violation_words(text)
        if violations:
            result["warnings"].append(f"Detected inappropriate words: {', '.join(violations[:3])}...")
        result["cleaned_text"] = censor_text(text)
    
    # Basic spam check (only if spam detection is enabled)
    if settings.ENABLE_SPAM_DETECTION and len(set(text.replace(" ", ""))) < 3 and len(text) > 10:
        result["warnings"].append("Review content appears to be spam (repeated characters)")
    
    return result
