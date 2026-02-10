# AGENCY_OBJECTS – Step 3

This package is the "agency-owned" runtime layer:
- Object schema (Object + elementlist)
- Method objects with hooks + optional permissions gates
- Scenario objects (composed methods)
- MRG (Global Recursive Engine) executes `how` over `what`
- Walker (recursive traversal) used by MRG to apply execution over nested dict-like structures
- CLI (`agency-objects`) with workspace support

Constraints:
- No resolver layer
- Everything is object-driven
- Permissions live on methods/scenarios (not on objects)
- getOrCreate implemented as a Scenario (get -> on failure create if allowed)
