"""
Output formatter for People Chat.
Transforms query results into beautiful terminal output (tables, charts, text).
"""

from typing import Any, Dict, List, Optional, Tuple
from io import StringIO
import os
import tempfile
import webbrowser


# ─── Terminal Table Formatting ──────────────────────────

def format_table(columns: List[str], rows: List[Dict[str, Any]], title: Optional[str] = None) -> str:
    """
    Format query results as a beautiful terminal table using rich.
    Falls back to simple text if rich isn't available.
    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        
        console = Console(file=StringIO(), width=120, force_terminal=True, color_system="truecolor")
        
        rich_table = Table(title=title, title_style="bold cyan", border_style="blue")
        
        for col in columns:
            rich_table.add_column(str(col), style="cyan", overflow="fold")
        
        for row in rows[:100]:  # Cap at 100 rows for display
            formatted_row = []
            for col in columns:
                val = row.get(col, "")
                if val is None:
                    formatted_row.append("—")
                elif isinstance(val, float):
                    formatted_row.append(f"{val:,.2f}")
                elif isinstance(val, int):
                    formatted_row.append(f"{val:,}")
                else:
                    formatted_row.append(str(val))
            rich_table.add_row(*formatted_row)
        
        console.print(rich_table)
        output = console.file.getvalue()
        
        if len(rows) > 100:
            output += f"\n  [dim]... and {len(rows) - 100} more rows[/dim]\n"
        
        return output
    
    except ImportError:
        # Fallback text table
        return _format_table_text(columns, rows, title)


def _format_table_text(columns: List[str], rows: List[Dict[str, Any]], title: Optional[str] = None) -> str:
    """Simple text-based table fallback."""
    lines = []
    if title:
        lines.append(f"\n{'='*60}")
        lines.append(f"  {title}")
        lines.append(f"{'='*60}")
    
    if not rows:
        lines.append("  (no results)")
        return '\n'.join(lines)
    
    # Calculate column widths
    widths = {}
    for col in columns:
        max_width = len(str(col))
        for row in rows[:100]:
            val = row.get(col, "")
            max_width = max(max_width, len(str(val)))
        widths[col] = min(max_width + 2, 60)
    
    # Header
    header = "  " + "".join(f"{str(col):{widths[col]}}" for col in columns)
    lines.append(header)
    lines.append("  " + "-" * sum(widths.values()))
    
    # Rows
    for row in rows[:100]:
        line = "  " + "".join(f"{str(row.get(col, '')):{widths[col]}}" for col in columns)
        lines.append(line)
    
    if len(rows) > 100:
        lines.append(f"  ... and {len(rows) - 100} more rows")
    
    lines.append(f"  ({len(rows[:100])} rows)\n")
    return '\n'.join(lines)


# ─── Chart Detection ─────────────────────────────────────

def _is_chartable(columns: List[str], rows: List[Dict[str, Any]]) -> bool:
    """Determine if results would make a good chart."""
    if not rows or len(rows) < 2:
        return False
    
    # Count numeric columns
    numeric_count = 0
    text_count = 0
    for col in columns:
        if rows[0].get(col) is None:
            continue
        if isinstance(rows[0][col], (int, float)):
            numeric_count += 1
        elif isinstance(rows[0][col], str) and len(rows) < 20:
            text_count += 1
    
    # Good for chart: 1+ text column + 1+ numeric column, < 20 rows
    return text_count >= 1 and numeric_count >= 1 and len(rows) <= 20


def _detect_chart_type(columns: List[str], rows: List[Dict[str, Any]]) -> str:
    """Auto-detect the best chart type for this data."""
    numeric_cols = []
    text_cols = []
    for col in columns:
        val = rows[0].get(col) if rows else None
        if isinstance(val, (int, float)):
            numeric_cols.append(col)
        elif val is not None:
            text_cols.append(col)
    
    category_col = text_cols[0] if text_cols else columns[0]
    value_col = numeric_cols[0] if numeric_cols else columns[1] if len(columns) > 1 else columns[0]
    
    # Check if there's a date/time column
    date_keywords = ['date', 'year', 'month', 'time', 'hire', 'termination']
    for col in columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in date_keywords) and len(numeric_cols) >= 1:
            return "line"
    
    # Bar chart for category comparisons (default)
    return "bar"


# ─── Chart Generation ───────────────────────────────────

def generate_chart(columns: List[str], rows: List[Dict[str, Any]], chart_type: Optional[str] = None) -> Optional[str]:
    """
    Generate a Plotly chart from query results.
    
    Returns: HTML string of the chart, or None if chart generation fails.
    """
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import pandas as pd
    except ImportError:
        return None
    
    if not rows:
        return None
    
    if chart_type is None:
        chart_type = _detect_chart_type(columns, rows)
    
    # Build DataFrame from results
    df = pd.DataFrame(rows)
    
    # Identify numeric and text columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if not numeric_cols or not text_cols:
        return None
    
    x_col = text_cols[0]
    y_col = numeric_cols[0]
    
    try:
        if chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, text_auto=True,
                        title=f"{y_col} by {x_col}",
                        color=y_col, color_continuous_scale='Viridis')
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_tickangle=-45)
            
        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, markers=True,
                         title=f"{y_col} Over Time" if 'time' in x_col.lower() else f"{y_col} by {x_col}")
            fig.update_layout(xaxis_tickangle=-45)
            
        elif chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_col,
                        title=f"{y_col} Distribution")
            
        else:
            fig = px.bar(df, x=x_col, y=y_col, text_auto=True,
                        title=f"{y_col} by {x_col}")
        
        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=40, r=40, t=40, b=40),
            height=400 + min(len(rows) * 20, 200),
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=False)
    
    except Exception:
        return None


def save_and_open_chart(html_content: str, filename: str = "people_chart.html") -> str:
    """Save chart HTML to a temp file and open in browser. Returns the file path."""
    output_dir = os.path.join(tempfile.gettempdir(), "people_chat")
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>People Chat — Chart</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
</head>
<body style="background: #1a1a2e; margin: 0; padding: 20px;">
    {html_content}
    <p style="color: #888; text-align: center; font-family: sans-serif; font-size: 12px;">
        Generated by People Chat · Close this tab when done
    </p>
</body>
</html>"""
    
    with open(filepath, 'w') as f:
        f.write(full_html)
    
    webbrowser.open(f'file://{filepath}')
    return filepath


# ─── Result Dispatcher ───────────────────────────────────

def format_result(
    query_result: Dict[str, Any],
    show_sql: bool = False,
    force_chart: bool = False,
) -> Dict[str, Any]:
    """
    Format a query result for display.
    
    Args:
        query_result: Result dict from query_engine.ask()
        show_sql: Whether to include the SQL query in output
    
    Returns:
        Dict with: text (terminal output), chart_html (optional), chart_path (optional)
    """
    output_parts = []
    chart_html = None
    chart_path = None
    
    # Error / needs_info case
    if not query_result.get("success", False):
        explanation = query_result.get("explanation", "I couldn't answer that question.")
        if query_result.get("needs_info"):
            output_parts.append(f"\n[bold yellow]ℹ️  {explanation}[/bold yellow]")
        else:
            error = query_result.get("error", "Unknown error")
            output_parts.append(f"\n[bold red]❌ {error}[/bold red]")
        
        if show_sql and query_result.get("sql"):
            output_parts.append(f"\n[dim]SQL: {query_result['sql']}[/dim]")
        
        return {
            "text": '\n'.join(output_parts),
            "chart_html": None,
            "chart_path": None,
        }
    
    # Success case
    results = query_result.get("results", {})
    columns = results.get("columns", [])
    rows = results.get("rows", [])
    explanation = query_result.get("explanation", "")
    intent = query_result.get("intent", "auto")
    
    # Format as table
    table = format_table(columns, rows)
    output_parts.append(table)
    
    # Add explanation
    if explanation and explanation != f"Query returned {len(rows)} rows.":
        output_parts.append(f"\n  {explanation}")
    
    # Format row count
    output_parts.append(f"\n  [dim]{len(rows)} row(s) returned[/dim]")
    
    # Add SQL if requested
    if show_sql and query_result.get("sql"):
        sql = query_result["sql"]
        output_parts.append(f"\n  [dim]── SQL ──[/dim]")
        output_parts.append(f"  [dim]{sql}[/dim]")
    
    # Generate chart if: force_chart, explicitly requested, or chartable data
    if force_chart:
        should_chart = bool(columns and rows)
    else:
        should_chart = intent == "chart" or (intent == "auto" and _is_chartable(columns, rows))
    
    if should_chart and columns and rows:
        chart_type = "bar" if intent != "chart" else None
        chart_html = generate_chart(columns, rows, chart_type)
        if chart_html:
            chart_path = save_and_open_chart(chart_html)
            output_parts.append(f"\n  [green]📈 Chart opened in browser[/green]")
    
    return {
        "text": '\n'.join(output_parts),
        "chart_html": chart_html,
        "chart_path": chart_path,
        "rows": len(rows),
    }


def format_without_rich(text: str) -> str:
    """Strip rich markup tags for plain terminal or log output."""
    import re
    text = re.sub(r'\[/?\w+\]', '', text)
    text = re.sub(r'\[/?\w+\s*\w*\]', '', text)
    return text
