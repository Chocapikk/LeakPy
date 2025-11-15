"""
MIT License

Copyright (c) 2025 Valentin Lobstein (balgogan@protonmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json

# ========================================================================
# BULK PROCESSING
# ========================================================================

def process_bulk_lines(response, log_func=None):
    """Process lines from bulk response stream."""
    if not response:
        return []
    
    # Parse JSON lines in a single pass, extracting events directly
    events = []
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        
        text = line.strip()
        if not text or not (text.startswith('{') or text.startswith('[')):
            continue
        
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "events" in parsed:
                events_list = parsed.get("events", [])
                if events_list:
                    events.extend(events_list)
        except (json.JSONDecodeError, TypeError):
            continue
    
    if not events:
        if log_func:
            log_func("No results returned from bulk query.", "warning")
        return []
    
    return events

