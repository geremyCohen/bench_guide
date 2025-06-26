#!/usr/bin/env python3
"""
HTML Report Generator

Generates HTML reports from benchmark results.
"""

import os
import json
from pathlib import Path
from datetime import datetime


def create_report(results, run_dir):
    """
    Create HTML report from benchmark results.
    
    Args:
        results (dict): Benchmark results by instance
        run_dir (Path): Directory containing result files
        
    Returns:
        str: Path to the generated report
    """
    report_path = run_dir / "report.html"
    
    # Create HTML content
    html = generate_html(results)
    
    # Write HTML to file
    with open(report_path, 'w') as f:
        f.write(html)
    
    return str(report_path)


def generate_html(results):
    """Generate HTML content for the report."""
    # Start with HTML header
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333;
        }
        .benchmark {
            margin-bottom: 30px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .chart-container {
            height: 400px;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        .system-info {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Benchmark Results</h1>
        <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
"""
    
    # Group results by benchmark type
    benchmarks = {}
    for instance_name, instance_results in results.items():
        for benchmark_type, benchmark_data in instance_results.items():
            if benchmark_type not in benchmarks:
                benchmarks[benchmark_type] = {}
            benchmarks[benchmark_type][instance_name] = benchmark_data
    
    # Generate content for each benchmark type
    for benchmark_type, benchmark_results in benchmarks.items():
        html += f'<div class="benchmark">\n'
        html += f'<h2>Benchmark: {benchmark_type}</h2>\n'
        
        # System information section
        html += '<div class="system-info">\n'
        html += '<h3>System Information</h3>\n'
        html += '<table>\n'
        html += '<tr><th>Instance</th><th>Architecture</th><th>CPU Model</th><th>CPU Cores</th></tr>\n'
        
        for instance_name, data in benchmark_results.items():
            arch = data.get("system_info", {}).get("architecture", "N/A")
            cpu_model = data.get("system_info", {}).get("cpu_model", "N/A")
            cpu_cores = data.get("system_info", {}).get("cpu_cores", "N/A")
            
            html += f'<tr><td>{instance_name}</td><td>{arch}</td><td>{cpu_model}</td><td>{cpu_cores}</td></tr>\n'
        
        html += '</table>\n'
        html += '</div>\n'
        
        # Generate charts based on benchmark type
        if benchmark_type == "100_cpu_utilization":
            html += generate_cpu_utilization_charts(benchmark_results)
            html += generate_mpstat_time_series_charts(benchmark_results)
        else:
            html += generate_generic_charts(benchmark_results, benchmark_type)
        
        html += '</div>\n'
    
    # Close HTML
    html += """
    </div>
    <script>
        // Initialize all charts
        document.addEventListener('DOMContentLoaded', function() {
            // Charts will be initialized by their specific functions
        });
    </script>
</body>
</html>
"""
    
    return html


def generate_cpu_utilization_charts(results):
    """Generate charts for CPU utilization benchmark."""
    html = ""
    
    # Check if we have run data
    has_runs = False
    run_names = set()
    for instance_name, data in results.items():
        if "runs" in data.get("metrics", {}):
            has_runs = True
            run_names.update(data.get("metrics", {}).get("runs", {}).keys())
    
    if has_runs and run_names:
        # Sort run names for consistent order
        run_names = sorted(run_names)
        
        # Generate a chart for each run type
        for i, run_name in enumerate(run_names):
            html += f'<h3>CPU Utilization - {run_name.replace("_", " ").title()}</h3>\n'
            html += f'<div class="chart-container"><canvas id="avgUtilChart_{i}"></canvas></div>\n'
            
            # Prepare data for the chart
            labels = []
            datasets = []
            
            for instance_name, data in results.items():
                labels.append(instance_name)
                run_data = data.get("metrics", {}).get("runs", {}).get(run_name, {})
                avg_util = run_data.get("avg_utilization", 0)
                datasets.append(avg_util)
            
            # Add mpstat time-series chart for this specific run
            html += generate_run_specific_mpstat_chart(results, run_name, i)
            
            # Add chart initialization script
            html += f"""
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const avgUtilCtx = document.getElementById('avgUtilChart_{i}').getContext('2d');
                    new Chart(avgUtilCtx, {{
                        type: 'bar',
                        data: {{
                            labels: {json.dumps(labels)},
                            datasets: [{{
                                label: '{run_name.replace("_", " ").title()} - CPU Utilization (%)',
                                data: {json.dumps(datasets)},
                                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                datalabels: {{
                                    anchor: 'end',
                                    align: 'top',
                                    formatter: function(value) {{
                                        return value.toFixed(1) + '%';
                                    }},
                                    font: {{
                                        weight: 'bold'
                                    }}
                                }}
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    max: 100
                                }}
                            }}
                        }},
                        plugins: [ChartDataLabels]
                    }});
                }});
            </script>
            """
    else:
        # Fallback to the old chart if no run data is available
        html += '<h3>Average CPU Utilization</h3>\n'
        html += '<div class="chart-container"><canvas id="avgUtilChart"></canvas></div>\n'
        
        # Prepare data for the chart
        labels = []
        datasets = []
        
        for instance_name, data in results.items():
            labels.append(instance_name)
            avg_util = data.get("metrics", {}).get("average_utilization", [0])
            if avg_util:
                datasets.append(avg_util[0])  # Use the first value
        
        # Add chart initialization script
        html += f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const avgUtilCtx = document.getElementById('avgUtilChart').getContext('2d');
                new Chart(avgUtilCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: [{{
                            label: 'Average CPU Utilization (%)',
                            data: {json.dumps(datasets)},
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});
            }});
        </script>
        """
    
    # Add comparison chart if we have multiple runs
    if has_runs and len(run_names) > 1:
        html += '<h3>CPU Utilization Comparison</h3>\n'
        html += '<div class="chart-container"><canvas id="comparisonChart"></canvas></div>\n'
        
        # Prepare data for the comparison chart
        datasets = []
        for i, run_name in enumerate(run_names):
            run_data = []
            for instance_name in results.keys():
                data = results[instance_name]
                avg_util = data.get("metrics", {}).get("runs", {}).get(run_name, {}).get("avg_utilization", 0)
                run_data.append(avg_util)
            
            # Generate a different color for each run
            color_idx = i % len(['red', 'blue', 'green', 'orange', 'purple', 'cyan'])
            color = ['red', 'blue', 'green', 'orange', 'purple', 'cyan'][color_idx]
            
            datasets.append({
                "label": run_name.replace("_", " ").title(),
                "data": run_data,
                "backgroundColor": f"rgba({','.join(map(str, [int(int(hash(color) % 255 * 0.7)), int(int(hash(color[::-1]) % 255 * 0.7)), int(int(hash(color + color) % 255 * 0.7)), 0.5]))})",
                "borderColor": f"rgba({','.join(map(str, [int(int(hash(color) % 255 * 0.7)), int(int(hash(color[::-1]) % 255 * 0.7)), int(int(hash(color + color) % 255 * 0.7)), 1]))})",
                "borderWidth": 1
            })
        
        # Add chart initialization script
        html += f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
                new Chart(comparisonCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(list(results.keys()))},
                        datasets: {json.dumps(datasets)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            datalabels: {{
                                anchor: 'end',
                                align: 'top',
                                formatter: function(value) {{
                                    return value.toFixed(1) + '%';
                                }},
                                font: {{
                                    weight: 'bold'
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }});
            }});
        </script>
        """
    
    return html


def generate_run_specific_mpstat_chart(results, run_name, chart_index):
    """Generate mpstat time-series chart for a specific run."""
    html = ""
    
    # Check if we have time-series data for this run
    mpstat_data = {}
    for instance_name, data in results.items():
        run_time_series = data.get("metrics", {}).get(f"time_series_{run_name}", [])
        if run_time_series:
            mpstat_data[instance_name] = run_time_series
        # Try generic time_series if run-specific not found
        elif not run_time_series:
            generic_time_series = data.get("metrics", {}).get("time_series", [])
            if generic_time_series:
                mpstat_data[instance_name] = generic_time_series
    
    if not mpstat_data:
        return html
    
    # Create a separate chart for each instance
    for i, (instance_name, time_series) in enumerate(mpstat_data.items()):
        # Check if detailed metrics are available
        has_detailed = len(time_series) > 0 and 'usr' in time_series[0]
        
        if has_detailed:
            html += f'<h4>{instance_name} - CPU Breakdown - {run_name.replace("_", " ").title()}</h4>\n'
            html += f'<div class="chart-container"><canvas id="mpstatChart_{instance_name}_{run_name}_{chart_index}"></canvas></div>\n'
            
            # Create stacked datasets for usr, sys, iowait
            stacked_metrics = ['usr', 'sys', 'iowait']
            stacked_labels = {'usr': 'User', 'sys': 'System', 'iowait': 'I/O Wait'}
            stacked_colors = {
                'usr': 'rgba(255, 99, 132, 0.7)',   # Red
                'sys': 'rgba(54, 162, 235, 0.7)',   # Blue
                'iowait': 'rgba(255, 206, 86, 0.7)' # Yellow
            }
            
            stacked_datasets = []
            for metric in stacked_metrics:
                chart_data = []
                for point in time_series:
                    if metric in point:
                        chart_data.append({'x': point['time'], 'y': point[metric]})
                
                if chart_data:
                    stacked_datasets.append({
                        'label': stacked_labels[metric],
                        'data': chart_data,
                        'backgroundColor': stacked_colors[metric],
                        'borderColor': stacked_colors[metric].replace('0.7', '1.0'),
                        'borderWidth': 1
                    })
            
            # Add total utilization as a line on top
            total_data = []
            for point in time_series:
                if 'utilization' in point:
                    total_data.append({'x': point['time'], 'y': point['utilization']})
            
            if total_data:
                stacked_datasets.append({
                    'label': 'Total CPU',
                    'data': total_data,
                    'type': 'line',
                    'borderColor': 'rgba(75, 192, 192, 1)',  # Teal
                    'backgroundColor': 'transparent',
                    'borderWidth': 2,
                    'fill': False,
                    'order': 0  # Draw on top
                })
            
            # Add chart initialization script
            html += f"""
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const mpstatCtx = document.getElementById('mpstatChart_{instance_name}_{run_name}_{chart_index}').getContext('2d');
                    new Chart(mpstatCtx, {{
                        type: 'bar',  // Default type for stacked bars
                        data: {{
                            datasets: {json.dumps(stacked_datasets)}
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {{
                                x: {{
                                    type: 'category',
                                    stacked: true,
                                    title: {{
                                        display: true,
                                        text: 'Time'
                                    }}
                                }},
                                y: {{
                                    stacked: true,
                                    beginAtZero: true,
                                    max: 100,
                                    title: {{
                                        display: true,
                                        text: 'CPU Utilization (%)'
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    display: true,
                                    position: 'top'
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false
                                }}
                            }}
                        }}
                    }});
                }});
            </script>
            """
        else:
            # Simple chart for total utilization only
            html += f'<h4>{instance_name} - CPU Utilization - {run_name.replace("_", " ").title()}</h4>\n'
            html += f'<div class="chart-container"><canvas id="mpstatChart_{instance_name}_{run_name}_{chart_index}"></canvas></div>\n'
            
            chart_data = []
            for point in time_series:
                chart_data.append({'x': point['time'], 'y': point.get('utilization', point.get('y', 0))})
            
            datasets = [{
                'label': 'Total CPU',
                'data': chart_data,
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'fill': True,
                'tension': 0.1,
                'borderWidth': 2
            }]
            
            html += f"""
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const mpstatCtx = document.getElementById('mpstatChart_{instance_name}_{run_name}_{chart_index}').getContext('2d');
                    new Chart(mpstatCtx, {{
                        type: 'line',
                        data: {{
                            datasets: {json.dumps(datasets)}
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {{
                                x: {{
                                    type: 'category',
                                    title: {{
                                        display: true,
                                        text: 'Time'
                                    }}
                                }},
                                y: {{
                                    beginAtZero: true,
                                    max: 100,
                                    title: {{
                                        display: true,
                                        text: 'CPU Utilization (%)'
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    display: true,
                                    position: 'top'
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false
                                }}
                            }}
                        }}
                    }});
                }});
            </script>
            """
    
    return html
    
    return html


def generate_mpstat_time_series_charts(results):
    """Generate time-series charts from mpstat data."""
    html = ""
    
    # Check if we have time-series data
    has_time_series = False
    for instance_name, data in results.items():
        if "time_series" in data.get("metrics", {}):
            has_time_series = True
            break
    
    if not has_time_series:
        return html
    
    html += '<h3>CPU Utilization Over Time</h3>\n'
    html += '<div class="chart-container"><canvas id="timeSeriesChart"></canvas></div>\n'
    
    # Prepare datasets for each instance
    datasets = []
    colors = ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 205, 86, 1)', 'rgba(75, 192, 192, 1)']
    
    for i, (instance_name, data) in enumerate(results.items()):
        time_series = data.get("metrics", {}).get("time_series", [])
        if time_series:
            chart_data = []
            for point in time_series:
                chart_data.append({
                    'x': point['time'],
                    'y': point['utilization']
                })
            
            color = colors[i % len(colors)]
            datasets.append({
                'label': instance_name,
                'data': chart_data,
                'borderColor': color,
                'backgroundColor': color.replace('1)', '0.1)'),
                'fill': False,
                'tension': 0.1
            })
    
    # Add chart initialization script
    html += f"""
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const timeSeriesCtx = document.getElementById('timeSeriesChart').getContext('2d');
            new Chart(timeSeriesCtx, {{
                type: 'line',
                data: {{
                    datasets: {json.dumps(datasets)}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            type: 'category',
                            title: {{
                                display: true,
                                text: 'Time'
                            }}
                        }},
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            title: {{
                                display: true,
                                text: 'CPU Utilization (%)'
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{
                            display: true
                        }}
                    }}
                }}
            }});
        }});
    </script>
    """
    
    return html


def generate_generic_charts(results, benchmark_type):
    """Generate charts for generic benchmark types."""
    html = ""
    
    # Find common metrics across all instances
    common_metrics = set()
    for instance_data in results.values():
        metrics = instance_data.get("metrics", {})
        for key in metrics:
            if isinstance(metrics[key], (int, float)):
                common_metrics.add(key)
    
    # Generate a chart for each common metric
    for metric in common_metrics:
        chart_id = f"chart_{metric}"
        html += f'<h3>Metric: {metric}</h3>\n'
        html += f'<div class="chart-container"><canvas id="{chart_id}"></canvas></div>\n'
        
        # Prepare data for the chart
        labels = []
        datasets = []
        
        for instance_name, data in results.items():
            labels.append(instance_name)
            value = data.get("metrics", {}).get(metric, 0)
            datasets.append(value)
        
        # Add chart initialization script
        html += f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const ctx = document.getElementById('{chart_id}').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: [{{
                            label: '{metric}',
                            data: {json.dumps(datasets)},
                            backgroundColor: 'rgba(75, 192, 192, 0.5)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            datalabels: {{
                                anchor: 'end',
                                align: 'top',
                                formatter: function(value) {{
                                    return value.toFixed(1);
                                }},
                                font: {{
                                    weight: 'bold'
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }},
                    plugins: [ChartDataLabels]
                }});
            }});
        </script>
        """
    
    return html