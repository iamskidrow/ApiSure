from typing import Dict, Any
from jinja2 import Template
from datetime import datetime


def generate_html_report(test_results: Dict[str, Any], output_file: str = "report.html") -> None:
    # HTML template using Jinja2
    template = Template('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Test Report</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
            h1, h2 { color: #2c3e50; }
            .summary { background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
            th { background-color: #3498db; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .test-case { background-color: #f9f9f9; padding: 15px; margin-bottom: 15px; border-left: 5px solid #3498db; }
            .test-case.passed { border-left-color: #2ecc71; }
            .test-case.failed { border-left-color: #e74c3c; }
            .skipped { border-left-color: #f39c12; }
            .details { margin-top: 10px; }
            .details p { margin: 5px 0; }
            .error { color: #e74c3c; }
            .warning { color: #f39c12; }
            .status-passed { color: #2ecc71; font-weight: bold; }
            .status-failed { color: #e74c3c; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>API Test Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Test Cases</td>
                    <td>{{ summary.total }}</td>
                </tr>
                <tr>
                    <td>Executed Test Cases</td>
                    <td>{{ summary.executed }}</td>
                </tr>
                <tr>
                    <td>Passed</td>
                    <td>{{ summary.passed }}</td>
                </tr>
                <tr>
                    <td>Failed</td>
                    <td>{{ summary.failed }}</td>
                </tr>
                <tr>
                    <td>Average Response Time</td>
                    <td>{{ summary.avg_response_time }}</td>
                </tr>
                <tr>
                    <td>Average Content Length</td>
                    <td>{{ summary.avg_content_length }}</td>
                </tr>
                <tr>
                    <td>Report Generated</td>
                    <td>{{ summary.timestamp }}</td>
                </tr>
            </table>
        </div>
        <h2>Test Case Details</h2>
        {% for test in test_cases %}
        <div class="test-case {{ test.status.lower() }}">
            <h3>Test Case {{ test.id }}: {{ test.description }}</h3>
            <table>
                <tr>
                    <th>Property</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Status</td>
                    <td class="status-{{ test.status.lower() }}">{{ test.status }}</td>
                </tr>
                <tr>
                    <td>Method</td>
                    <td>{{ test.method }}</td>
                </tr>
                <tr>
                    <td>URL</td>
                    <td>{{ test.url }}</td>
                </tr>
                <tr>
                    <td>Status Code</td>
                    <td>{{ test.status_code }}{% if test.expected_status %} (Expected: {{ test.expected_status }}){% endif %}</td>
                </tr>
                <tr>
                    <td>Response Time</td>
                    <td>{{ test.response_time }}</td>
                </tr>
                <tr>
                    <td>Content Length</td>
                    <td>{{ test.content_length }}</td>
                </tr>
            </table>
            {% if test.validation_results %}
            <div class="details">
                <h4>Validation Results</h4>
                <ul>
                {% for result in test.validation_results %}
                    <li class="{{ result.type }}">{{ result.message }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </body>
    </html>
    ''')

    # Prepare summary data for the report
    summary = {
        'total': test_results['total_tests'],
        'executed': test_results['executed_tests'],
        'passed': test_results['pass'],
        'failed': test_results['fail'],
        'avg_response_time': test_results['avg_response_time'],
        'avg_content_length': test_results['avg_content_length'],
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Prepare test cases data for the report
    test_cases = []
    for case in test_results['test_cases']:
        validation_results = []
        if 'validation_results' in case:
            for result in case['validation_results']:
                result_type = 'error' if not result['passed'] else 'warning' if 'warning' in result else ''
                validation_results.append({
                    'type': result_type,
                    'message': result['message']
                })

        test_cases.append({
            'id': case['id'],
            'description': case['description'],
            'method': case['method'],
            'url': case['url'],
            'status': 'Passed' if case['passed'] else 'Failed',
            'status_code': case.get('status_code'),
            'expected_status': case.get('expected_status'),
            'response_time': case.get('response_time'),
            'content_length': case.get('content_length'),
            'validation_results': validation_results
        })

    # Render the template with the prepared data
    html_content = template.render(summary=summary, test_cases=test_cases)

    # Write the rendered HTML to a file
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"HTML report generated: {output_file}")
