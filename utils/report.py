from typing import Dict, Any
from jinja2 import Template
from datetime import datetime


def generate_html_report(test_results: Dict[str, Any], output_file: str = "api_test_report.html") -> None:

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
            .test-case { background-color: #f9f9f9; padding: 15px; margin-bottom: 15px; border-left: 5px solid #3498db; }
            .pass { border-left-color: #2ecc71; }
            .fail { border-left-color: #e74c3c; }
            .skipped { border-left-color: #f39c12; }
            .details { margin-top: 10px; }
            .details p { margin: 5px 0; }
            .error { color: #e74c3c; }
            .warning { color: #f39c12; }
        </style>
    </head>
    <body>
        <h1>API Test Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p>Total Test Cases: {{ summary.total }}</p>
            <p>Executed Test Cases: {{ summary.executed }}</p>
            <p>Passed: {{ summary.passed }}</p>
            <p>Failed: {{ summary.failed }}</p>
            <p>Average Response Time: {{ summary.avg_response_time }}</p>
            <p>Average Content Length: {{ summary.avg_content_length }}</p>
            <p>Report Generated: {{ summary.timestamp }}</p>
        </div>
        <h2>Test Case Details</h2>
        {% for test in test_cases %}
        <div class="test-case {{ test.status.lower() }}">
            <h3>Test Case {{ test.id }}: {{ test.description }}</h3>
            <p>Status: {{ test.status }}</p>
            <div class="details">
                <p>Method: {{ test.method }}</p>
                <p>URL: {{ test.url }}</p>
                <p>Status Code: {{ test.status_code }}{% if test.expected_status %} (Expected: {{ test.expected_status }}){% endif %}</p>
                <p>Response Time: {{ test.response_time }}</p>
                <p>Content Length: {{ test.content_length }}</p>
                {% if test.validation_results %}
                    {% for result in test.validation_results %}
                        <p class="{{ result.type }}">{{ result.message }}</p>
                    {% endfor %}
                {% endif %}
            </div>
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
