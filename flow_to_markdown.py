#!/usr/bin/env python3
"""
Convert mitmdump flow file to markdown documentation with example requests
Usage: python flow_to_markdown.py input.mitm output.md [--filter PATTERN] [--exclude PATTERN]

Examples:
  python flow_to_markdown.py flows.mitm output.md
  python flow_to_markdown.py flows.mitm output.md --filter "/api/*"
  python flow_to_markdown.py flows.mitm output.md --filter "/api/users/*" "/api/posts/*"
  python flow_to_markdown.py flows.mitm output.md --filter "/api/*" --exclude "*/internal/*"
"""

import sys
import json
import re
import argparse
from mitmproxy import io, http
from mitmproxy.exceptions import FlowReadException


def matches_pattern(path, patterns):
    """Check if path matches any of the given patterns"""
    if not patterns:
        return True  # No filter means include all

    for pattern in patterns:
        # Support both regex and simple wildcard patterns
        if '*' in pattern or '?' in pattern:
            # Convert wildcard to regex
            regex_pattern = pattern.replace('.', r'\.').replace('*', '.*').replace('?', '.')
            if re.search(regex_pattern, path):
                return True
        else:
            # Direct substring match or regex
            try:
                if re.search(pattern, path):
                    return True
            except re.error:
                # If regex fails, try substring match
                if pattern in path:
                    return True

    return False


def should_include_flow(path, include_patterns, exclude_patterns):
    """Determine if a flow should be included based on include/exclude patterns"""
    # If there are include patterns, path must match at least one
    if include_patterns and not matches_pattern(path, include_patterns):
        return False

    # If there are exclude patterns, path must not match any
    if exclude_patterns and matches_pattern(path, exclude_patterns):
        return False

    return True


def format_headers(headers):
    """Format headers as markdown code block"""
    if not headers:
        return ""

    lines = []
    for key, value in headers.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def format_body(content, content_type=""):
    """Format request/response body with appropriate syntax highlighting"""
    if not content:
        return "*No body*"

    try:
        # Try to parse as JSON
        parsed = json.loads(content)
        return f"```json\n{json.dumps(parsed, indent=2)}\n```"
    except:
        pass

    # Check content type for syntax highlighting
    if "json" in content_type.lower():
        return f"```json\n{content}\n```"
    elif "xml" in content_type.lower() or "html" in content_type.lower():
        return f"```xml\n{content}\n```"
    elif "javascript" in content_type.lower():
        return f"```javascript\n{content}\n```"
    else:
        return f"```\n{content}\n```"


def flow_to_markdown(flow: http.HTTPFlow):
    """Convert a single flow to markdown format"""
    md = []

    # Title with method and URL
    md.append(f"## {flow.request.method} {flow.request.pretty_url}")
    md.append("")

    # Request section
    md.append("### Request")
    md.append("")

    # Request line
    md.append(f"**{flow.request.method}** `{flow.request.path}`")
    md.append("")

    # Host info
    md.append(f"**Host:** `{flow.request.host}:{flow.request.port}`")
    md.append("")

    # Request headers
    md.append("**Headers:**")
    md.append("```")
    md.append(format_headers(flow.request.headers))
    md.append("```")
    md.append("")

    # Query parameters
    if flow.request.query:
        md.append("**Query Parameters:**")
        for key, value in flow.request.query.items():
            md.append(f"- `{key}`: `{value}`")
        md.append("")

    # Request body
    if flow.request.content:
        md.append("**Body:**")
        content_type = flow.request.headers.get("content-type", "")
        body_text = flow.request.content.decode('utf-8', errors='ignore')
        md.append(format_body(body_text, content_type))
        md.append("")

    # Response section (if available)
    if flow.response:
        md.append("### Response")
        md.append("")

        # Status
        md.append(f"**Status:** `{flow.response.status_code} {flow.response.reason}`")
        md.append("")

        # Response headers
        md.append("**Headers:**")
        md.append("```")
        md.append(format_headers(flow.response.headers))
        md.append("```")
        md.append("")

        # Response body
        if flow.response.content:
            md.append("**Body:**")
            content_type = flow.response.headers.get("content-type", "")
            body_text = flow.response.content.decode('utf-8', errors='ignore')
            md.append(format_body(body_text, content_type))
            md.append("")

    # cURL example
    md.append("### cURL Example")
    md.append("")
    curl = generate_curl(flow)
    md.append("```bash")
    md.append(curl)
    md.append("```")
    md.append("")

    md.append("---")
    md.append("")

    return "\n".join(md)


def generate_curl(flow: http.HTTPFlow):
    """Generate cURL command from flow"""
    curl = f"curl -X {flow.request.method} '{flow.request.pretty_url}'"

    # Add headers
    for key, value in flow.request.headers.items():
        if key.lower() not in ['host', 'content-length', 'connection']:
            curl += f" \\\n  -H '{key}: {value}'"

    # Add body
    if flow.request.content:
        body = flow.request.content.decode('utf-8', errors='ignore')
        # Escape single quotes in body
        body = body.replace("'", "'\\''")
        curl += f" \\\n  -d '{body}'"

    return curl


def convert_flow_file(input_file, output_file, include_patterns=None, exclude_patterns=None):
    """Convert entire flow file to markdown"""
    try:
        with open(input_file, "rb") as f:
            flow_reader = io.FlowReader(f)

            markdown = []
            markdown.append("# HTTP Request Examples")
            markdown.append("")
            markdown.append(f"*Generated from: {input_file}*")

            if include_patterns:
                markdown.append(f"*Include patterns: {', '.join(f'`{p}`' for p in include_patterns)}*")
            if exclude_patterns:
                markdown.append(f"*Exclude patterns: {', '.join(f'`{p}`' for p in exclude_patterns)}*")

            markdown.append("")
            markdown.append("---")
            markdown.append("")

            count = 0
            skipped = 0

            for flow in flow_reader.stream():
                if isinstance(flow, http.HTTPFlow):
                    # Apply path filter
                    if should_include_flow(flow.request.path, include_patterns, exclude_patterns):
                        markdown.append(flow_to_markdown(flow))
                        count += 1
                    else:
                        skipped += 1

            # Write to output file
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write("\n".join(markdown))

            print(f"Successfully converted {count} flows to {output_file}")
            if skipped > 0:
                print(f"   Skipped {skipped} flows (didn't match filters)")

    except FlowReadException as e:
        print(f"Error reading flow file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert mitmdump flow file to markdown documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Convert all requests
  python flow_to_markdown.py flows.mitm output.md
  
  # Filter by specific paths (include only)
  python flow_to_markdown.py flows.mitm output.md --filter /api/ /v1/users
  
  # Use wildcards
  python flow_to_markdown.py flows.mitm output.md --filter "/api/*" "*/auth/*"
  
  # Use regex patterns
  python flow_to_markdown.py flows.mitm output.md --filter "^/api/v[0-9]+/" "/users/[0-9]+$"
  
  # Exclude certain paths
  python flow_to_markdown.py flows.mitm output.md --exclude "/health" "/metrics"
  
  # Combine include and exclude
  python flow_to_markdown.py flows.mitm output.md --filter "/api/*" --exclude "*/internal/*"
        '''
    )

    parser.add_argument('input', help='Input mitmdump flow file (.mitm)')
    parser.add_argument('output', help='Output markdown file (.md)')
    parser.add_argument(
        '--filter', '-f',
        nargs='+',
        metavar='PATTERN',
        help='Path patterns to include (supports wildcards * and ? or regex)'
    )
    parser.add_argument(
        '--exclude', '-e',
        nargs='+',
        metavar='PATTERN',
        help='Path patterns to exclude (supports wildcards * and ? or regex)'
    )

    args = parser.parse_args()

    convert_flow_file(args.input, args.output, args.filter, args.exclude)