"""
EURKAI_COCKPIT — Storage Package
Version: 1.0.0

Provides SQLite storage layer with CRUD operations.
"""

from .storage import (
    # Config
    DEFAULT_DB_PATH,
    ENCRYPTION_KEY_ENV,
    
    # Utilities
    generate_uuid,
    utc_now,
    
    # Encryption
    SecretEncryption,
    
    # Data classes
    Project,
    Brief,
    Run,
    Config,
    Secret,
    ModuleManifest,
    Module,
    Backup,
    
    # Main storage class
    Storage,
)

from .migrations import (
    SCHEMA_VERSION,
    get_schema_version,
    init_database,
    migrate,
    reset_database,
)

__all__ = [
    # Config
    "DEFAULT_DB_PATH",
    "ENCRYPTION_KEY_ENV",
    
    # Utilities
    "generate_uuid",
    "utc_now",
    
    # Encryption
    "SecretEncryption",
    
    # Data classes
    "Project",
    "Brief",
    "Run",
    "Config",
    "Secret",
    "ModuleManifest",
    "Module",
    "Backup",
    
    # Main storage class
    "Storage",
    
    # Migrations
    "SCHEMA_VERSION",
    "get_schema_version",
    "init_database",
    "migrate",
    "reset_database",
]

__version__ = "1.0.0"
