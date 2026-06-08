"""LLM Airflow DAG generator."""
from langchain_google_vertexai import ChatVertexAI
from datetime import datetime

DAG_TEMPLATE_CONTEXT = """
You are an Apache Airflow expert (version 2.9+). Generate production-ready DAG code.
Requirements:
- Use TaskFlow API (@task decorator) when possible
- Add proper retries (retries=3, retry_delay=5min) on all tasks
- Include SLA alerts (sla=timedelta(hours=1)) for critical tasks  
- Add on_failure_callback with Slack notification
- Use sensors where appropriate (FileSensor, ExternalTaskSensor)
- Parametrize with Variable.get() for environment-specific values
- Add docstring with DAG description
- Use proper scheduling (cron expression)
- Return ONLY the Python code, no markdown
"""

class AirflowDAGGenerator:
    def __init__(self):
        self.llm = ChatVertexAI(model_name="gemini-1.5-pro-002", temperature=0.1)

    def generate(self, description: str, dag_id: str = None) -> str:
        if not dag_id:
            dag_id = f"generated_dag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        prompt = f"{DAG_TEMPLATE_CONTEXT}\n\nDAG ID: {dag_id}\n\nPipeline description:\n{description}\n\nPython code:"
        code = self.llm.invoke(prompt).content
        if "```python" in code: code = code.split("```python")[1].split("```")[0]
        return code.strip()

    def validate_dag(self, dag_code: str) -> dict:
        """Basic validation of generated DAG."""
        import ast
        errors = []
        try: ast.parse(dag_code)
        except SyntaxError as e: errors.append(f"Syntax error: {e}")
        required = ["from airflow", "dag_id", "schedule"]
        for req in required:
            if req not in dag_code: errors.append(f"Missing: {req}")
        return {"valid": len(errors) == 0, "errors": errors}
