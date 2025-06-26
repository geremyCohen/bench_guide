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