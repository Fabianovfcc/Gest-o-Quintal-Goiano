import re
import os

filepath = 'backend/app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Protect all /api/ routes except auth and status
# Find all @app.route("/api/...") decorators
# and insert @api_key_required right below them, if not already there.

def replacer(match):
    full_match = match.group(0)
    route_path = match.group(1)
    
    # Exceptions
    if route_path in ['/api/status', '/api/auth/login', '/api/auth/logout', '/api/auth/verificar']:
        return full_match
        
    # If already protected
    if '@api_key_required' in full_match or '@jwt_required' in full_match:
        return full_match
        
    # Add rate limits for specific routes
    limit_str = ""
    if route_path == '/api/ocr/nota':
        limit_str = '\n@limiter.limit("20 per hour")'
    elif route_path == '/api/nfe/preview':
        limit_str = '\n@limiter.limit("30 per hour")'
    elif route_path == '/api/relatorio/pdf':
        limit_str = '\n@limiter.limit("10 per hour")'
        
    # Insert decorators
    # match.group(0) is the @app.route(...) line
    # We want to append @api_key_required\n
    return f'{full_match}\n@api_key_required{limit_str}'

new_content = re.sub(r'@app\.route\("(/api/[^"]+)"(?:,\s*methods=\[.*?\])?\)', replacer, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated routes in app.py successfully.")
