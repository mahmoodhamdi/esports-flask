"""
Search Engine Configuration
Centralized configuration for the enhanced search system
"""

import os
import logging
from typing import Dict, List, Any

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': 'search.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

# Search engine limits and constraints
SEARCH_LIMITS = {
    'MIN_QUERY_LENGTH': 2,
    'MAX_QUERY_LENGTH': 500,
    'MAX_PER_PAGE': 100,
    'DEFAULT_PER_PAGE': 10,
    'MAX_PAGE_NUMBER': 10000,
    'MAX_RESULTS_PER_TABLE': 1000,
    'MAX_SUGGESTIONS': 20,
    'DEFAULT_SUGGESTIONS': 5,
    'SEARCH_TIMEOUT': 30.0,  # seconds
}

# Security configuration
SECURITY_CONFIG = {
    'RATE_LIMIT_ENABLED': True,
    'RATE_LIMIT_REQUESTS': 100,  # requests per minute
    'RATE_LIMIT_STORAGE': 'memory',
    'SQL_INJECTION_PROTECTION': True,
    'XSS_PROTECTION': True,
    'INPUT_SANITIZATION': True,
    'DANGEROUS_PATTERNS': [
        r'(\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|UNION|SELECT)\b)',
        r'(--|\#|\/\*|\*\/)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\'\s*(OR|AND)\s*\'\d+\'\s*=\s*\'\d+)',
        r'(\bSCRIPT\b|\bONLOAD\b|\bONERROR\b)',
        r'(<script|<iframe|<object|<embed|javascript:)',
    ]
}

# Database configuration
DATABASE_CONFIG = {
    'DATABASE_NAME': 'news.db',
    'CONNECTION_TIMEOUT': 30.0,
    'ENABLE_WAL_MODE': True,
    'ENABLE_FOREIGN_KEYS': True,
    'CACHE_SIZE': 10000,
    'TEMP_STORE': 'memory',
    'MMAP_SIZE': 134217728,  # 128MB
    'ENABLE_FTS': True,
    'AUTO_VACUUM': 'incremental',
    'SYNCHRONOUS': 'normal',
}

# Search types and their configurations
SEARCH_TYPES_CONFIG = {
    "news": {
        "table": "news",
        "type": "sql",
        "search_fields": ["title", "description", "writer"],
        "filter_fields": ["writer"],
        "sortable_fields": ["created_at", "updated_at", "title"],
        "default_sort": "created_at DESC",
        "enable_fts": True,
        "boost_fields": {"title": 2.0, "description": 1.0, "writer": 1.5},
    },
    "teams": {
        "table": "teams",
        "type": "sql",
        "search_fields": ["team_name"],
        "filter_fields": ["team_name"],
        "sortable_fields": ["team_name", "updated_at"],
        "default_sort": "team_name ASC",
        "enable_fts": False,
        "boost_fields": {"team_name": 2.0},
    },
    "events": {
        "table": "events",
        "type": "sql",
        "search_fields": ["name"],
        "filter_fields": ["name"],
        "sortable_fields": ["name", "updated_at"],
        "default_sort": "updated_at DESC",
        "enable_fts": False,
        "boost_fields": {"name": 2.0},
    },
    "games": {
        "table": "games",
        "type": "sql",
        "search_fields": ["game_name", "description", "genre", "platform"],
        "filter_fields": ["genre", "platform"],
        "sortable_fields": ["game_name", "genre", "platform", "updated_at"],
        "default_sort": "game_name ASC",
        "enable_fts": True,
        "boost_fields": {"game_name": 2.0, "genre": 1.5, "platform": 1.5, "description": 1.0},
    },
    "matches": {
        "table": "matches",
        "type": "sql",
        "search_fields": ["team1_name", "team2_name", "game", "tournament", "group_name"],
        "filter_fields": ["game", "tournament", "group_name"],
        "sortable_fields": ["match_date", "updated_at", "game"],
        "default_sort": "match_date DESC",
        "enable_fts": False,
        "boost_fields": {"team1_name": 2.0, "team2_name": 2.0, "game": 1.5, "tournament": 1.5},
    },
    "players": {
        "table": "player_information",
        "type": "json",
        "search_fields": ["Name", "Player_Information.Romanized Name"],
        "filter_fields": ["Nationality"],
        "sortable_fields": ["Name"],
        "default_sort": "Name ASC",
        "enable_fts": False,
        "boost_fields": {"Name": 2.0, "Player_Information.Romanized Name": 1.5},
        "json_search_paths": {
            "Name": "$.Name",
            "Romanized Name": "$.Player_Information.\"Romanized Name\"",
            "Nationality": "$.Player_Information.Nationality.text"
        }
    }
}

# Performance optimization settings
PERFORMANCE_CONFIG = {
    'ENABLE_CACHING': True,
    'CACHE_TTL': 300,  # 5 minutes
    'ENABLE_QUERY_OPTIMIZATION': True,
    'ENABLE_RESULT_COMPRESSION': True,
    'PARALLEL_SEARCH_ENABLED': False,  # Can be enabled for very large datasets
    'SEARCH_RESULT_POOLING': True,
    'LAZY_LOADING': True,
    'PREFETCH_RELATED': True,
}

# API Response configuration
API_CONFIG = {
    'INCLUDE_METADATA': True,
    'INCLUDE_SEARCH_INFO': True,
    'INCLUDE_PAGINATION': True,
    'INCLUDE_TIMING': True,
    'STANDARDIZED_RESPONSES': True,
    'ERROR_CODES': {
        'INVALID_PARAMS': 'INVALID_PARAMS',
        'MISSING_QUERY': 'MISSING_QUERY',
        'QUERY_TOO_SHORT': 'QUERY_TOO_SHORT',
        'QUERY_TOO_LONG': 'QUERY_TOO_LONG',
        'SEARCH_ERROR': 'SEARCH_ERROR',
        'GLOBAL_SEARCH_ERROR': 'GLOBAL_SEARCH_ERROR',
        'RATE_LIMIT_EXCEEDED': 'RATE_LIMIT_EXCEEDED',
        'INTERNAL_ERROR': 'INTERNAL_ERROR',
        'NOT_FOUND': 'NOT_FOUND',
        'METHOD_NOT_ALLOWED': 'METHOD_NOT_ALLOWED',
    }
}

# Monitoring and analytics
MONITORING_CONFIG = {
    'ENABLE_METRICS': True,
    'TRACK_SEARCH_QUERIES': True,
    'TRACK_RESPONSE_TIMES': True,
    'TRACK_ERROR_RATES': True,
    'ENABLE_HEALTH_CHECKS': True,
    'METRICS_RETENTION_DAYS': 30,
    'ALERT_THRESHOLDS': {
        'ERROR_RATE': 0.05,  # 5%
        'RESPONSE_TIME_MS': 1000,
        'SEARCH_FAILURE_RATE': 0.02,  # 2%
    }
}

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_FUZZY_SEARCH': True,
    'ENABLE_AUTOCOMPLETE': True,
    'ENABLE_SEARCH_SUGGESTIONS': True,
    'ENABLE_ADVANCED_FILTERS': True,
    'ENABLE_SEARCH_HISTORY': False,
    'ENABLE_SEARCH_ANALYTICS': True,
    'ENABLE_RESULT_HIGHLIGHTING': True,
    'ENABLE_SPELL_CORRECTION': False,  # Requires additional libraries
    'ENABLE_SEMANTIC_SEARCH': False,  # Requires ML libraries
}

# Environment-specific configurations
def get_config_for_environment(env: str = None) -> Dict[str, Any]:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    configs = {
        'development': {
            'DEBUG': True,
            'TESTING': False,
            'LOG_LEVEL': 'DEBUG',
            'ENABLE_QUERY_LOGGING': True,
            'STRICT_VALIDATION': False,
        },
        'testing': {
            'DEBUG': False,
            'TESTING': True,
            'LOG_LEVEL': 'INFO',
            'ENABLE_QUERY_LOGGING': False,
            'STRICT_VALIDATION': True,
            'DATABASE_NAME': 'test_news.db',
        },
        'production': {
            'DEBUG': False,
            'TESTING': False,
            'LOG_LEVEL': 'WARNING',
            'ENABLE_QUERY_LOGGING': False,
            'STRICT_VALIDATION': True,
            'ENABLE_CACHING': True,
            'RATE_LIMIT_ENABLED': True,
        }
    }
    
    return configs.get(env, configs['development'])

# Utility functions
def get_search_config(search_type: str) -> Dict[str, Any]:
    """Get configuration for a specific search type"""
    return SEARCH_TYPES_CONFIG.get(search_type, {})

def get_all_search_types() -> List[str]:
    """Get all supported search types"""
    return list(SEARCH_TYPES_CONFIG.keys())

def get_search_fields(search_type: str) -> List[str]:
    """Get search fields for a specific search type"""
    config = get_search_config(search_type)
    return config.get('search_fields', [])

def get_filter_fields(search_type: str) -> List[str]:
    """Get filter fields for a specific search type"""
    config = get_search_config(search_type)
    return config.get('filter_fields', [])

def is_json_search_type(search_type: str) -> bool:
    """Check if search type uses JSON data"""
    config = get_search_config(search_type)
    return config.get('type') == 'json'

def get_table_name(search_type: str) -> str:
    """Get table name for a search type"""
    config = get_search_config(search_type)
    return config.get('table', '')

def get_boost_fields(search_type: str) -> Dict[str, float]:
    """Get field boost values for relevance scoring"""
    config = get_search_config(search_type)
    return config.get('boost_fields', {})

# Configuration validation
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate search types
    for search_type, config in SEARCH_TYPES_CONFIG.items():
        if not config.get('table'):
            errors.append(f"Missing table name for search type: {search_type}")
        
        if not config.get('search_fields'):
            errors.append(f"Missing search fields for search type: {search_type}")
        
        if config.get('type') not in ['sql', 'json']:
            errors.append(f"Invalid type for search type: {search_type}")
    
    # Validate limits
    if SEARCH_LIMITS['MIN_QUERY_LENGTH'] <= 0:
        errors.append("MIN_QUERY_LENGTH must be positive")
    
    if SEARCH_LIMITS['MAX_QUERY_LENGTH'] <= SEARCH_LIMITS['MIN_QUERY_LENGTH']:
        errors.append("MAX_QUERY_LENGTH must be greater than MIN_QUERY_LENGTH")
    
    if SEARCH_LIMITS['MAX_PER_PAGE'] <= 0:
        errors.append("MAX_PER_PAGE must be positive")
    
    if SEARCH_LIMITS['DEFAULT_PER_PAGE'] <= 0:
        errors.append("DEFAULT_PER_PAGE must be positive")
    
    if SEARCH_LIMITS['MAX_PAGE_NUMBER'] <= 0:
        errors.append("MAX_PAGE_NUMBER must be positive")
    
    return errors