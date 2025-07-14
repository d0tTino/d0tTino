# json_schema_bench.py

import dspy
import pandas as pd
import json
import jsonschema
import time
import warnings
from typing import Dict, Any

# Suppress verbose warnings for a cleaner output
warnings.filterwarnings('ignore')

# --- 1. Schema Definitions ---
# Five diverse schemas inspired by JSONSchemaBench to test different aspects
# of structured data generation.

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "simple_user_profile": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "User Profile",
        "description": "A basic user profile with an ID, username, and active status.",
        "type": "object",
        "properties": {
            "id": {"type": "integer", "description": "The unique identifier for a user."},
            "username": {"type": "string", "description": "The user's chosen name."},
            "isActive": {"type": "boolean", "description": "Whether the user account is active."}
        },
        "required": ["id", "username", "isActive"]
    },
    "nested_product_catalog": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Product Catalog",
        "description": "A product with nested details for dimensions.",
        "type": "object",
        "properties": {
            "productId": {"type": "string", "pattern": "^[A-Z0-9]{8}$"},
            "productName": {"type": "string"},
            "price": {"type": "number", "exclusiveMinimum": 0},
            "dimensions": {
                "type": "object",
                "properties": {
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "depth": {"type": "number"}
                },
                "required": ["width", "height", "depth"]
            }
        },
        "required": ["productId", "productName", "price"]
    },
    "meeting_invite_with_attendees": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Meeting Invite",
        "description": "A meeting invitation that includes a list of attendee email addresses.",
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "dateTime": {"type": "string", "format": "date-time"},
            "attendees": {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "email"
                },
                "minItems": 1
            }
        },
        "required": ["topic", "dateTime", "attendees"]
    },
    "project_with_tasks": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Project Tasks",
        "description": "A project containing a list of tasks, where each task is an object.",
        "type": "object",
        "properties": {
            "projectName": {"type": "string"},
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "taskId": {"type": "integer"},
                        "description": {"type": "string"},
                        "isComplete": {"type": "boolean"}
                    },
                    "required": ["taskId", "description", "isComplete"]
                }
            }
        },
        "required": ["projectName", "tasks"]
    },
    "complex_api_response": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Complex API Response",
        "description": "A complex API response with various data types, enums, and required fields.",
        "type": "object",
        "properties": {
            "transactionId": {"type": "string", "format": "uuid"},
            "status": {"type": "string", "enum": ["success", "pending", "failed"]},
            "data": {
                "type": "array",
                "items": {"type": "object"}
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "source": {"type": "string"}
                },
                "required": ["timestamp"]
            }
        },
        "required": ["transactionId", "status", "data"]
    }
}

# --- 2. DSPy Signature Definition ---

class GenerateJSON(dspy.Signature):
    """
    Generate a JSON object that strictly adheres to the provided schema.
    The output must be a single, valid JSON object string without any extra text or explanations.
    """
    prompt = dspy.InputField(desc="A prompt describing the desired JSON content and its schema.")
    json_output = dspy.OutputField(desc="A valid JSON object string.")

# --- 3. Main Benchmark Logic ---

def main():
    """
    Runs the benchmark to test models' schema compliance.
    """
    print("--- Starting JSON Schema Compliance Benchmark ---")

    # Configure local models to be tested
    models_to_test = {
        'phi3:mini': dspy.OllamaLocal(model='phi3:mini', max_tokens=2048),
        'llama3:8b': dspy.OllamaLocal(model='llama3:8b', max_tokens=2048)
    }

    SAMPLES_PER_CONFIG = 20
    all_results = []

    for model_name, model_lm in models_to_test.items():
        dspy.settings.configure(lm=model_lm)
        
        for schema_name, schema_dict in SCHEMAS.items():
            print(f"\n--- Testing Model: '{model_name}' with Schema: '{schema_name}' ---")
            
            # Dynamically create a TypedPredictor with the current schema
            # This is the modern DSPy way to enforce typed/structured output.
            predictor = dspy.TypedPredictor(
                GenerateJSON,
                json_output=dspy.OutputField(
                    desc="A valid JSON object string.",
                    schema=schema_dict
                )
            )

            compliant_count = 0
            total_latency = 0
            total_token_count = 0
            
            prompt_for_schema = f"Generate a JSON object for a '{schema_name}'. The JSON must strictly conform to this schema:\n\n```json\n{json.dumps(schema_dict, indent=2)}\n```"

            for i in range(SAMPLES_PER_CONFIG):
                print(f"  Generating sample {i+1}/{SAMPLES_PER_CONFIG}...", end='\r')
                
                start_time = time.time()
                try:
                    # Generate the JSON output
                    prediction = predictor(prompt=prompt_for_schema)
                    generated_str = prediction.json_output
                    
                    # 1. Validate if the output is valid JSON
                    output_json = json.loads(generated_str)
                    
                    # 2. Validate the JSON against the schema
                    jsonschema.validate(instance=output_json, schema=schema_dict)
                    
                    # If both validations pass, it's compliant
                    compliant_count += 1
                    total_latency += (time.time() - start_time)
                    # Approximate token count (chars / 4 is a common heuristic)
                    total_token_count += len(generated_str) / 4

                except (json.JSONDecodeError, jsonschema.ValidationError, Exception):
                    # Any error in generation or validation means non-compliance
                    pass

            # Calculate metrics for this configuration
            compliance_percent = (compliant_count / SAMPLES_PER_CONFIG) * 100
            avg_latency = total_latency / compliant_count if compliant_count > 0 else 0
            avg_token_count = total_token_count / compliant_count if compliant_count > 0 else 0

            print(f"  Compliance: {compliance_percent:.1f}% ({compliant_count}/{SAMPLES_PER_CONFIG})")
            if compliant_count > 0:
                print(f"  Avg Latency (compliant): {avg_latency:.2f}s")
                print(f"  Avg Token Count (compliant): {avg_token_count:.0f}")

            all_results.append({
                'model': model_name,
                'schema_name': schema_name,
                'compliance_percent': compliance_percent,
                'avg_latency_s': avg_latency,
                'avg_token_count': avg_token_count
            })

    # --- 5. Save Results ---
    if not all_results:
        print("\nBenchmark finished with no results. Check model availability.")
        return

    results_df = pd.DataFrame(all_results)
    output_filename = 'schema_results.csv'
    results_df.to_csv(output_filename, index=False)

    print(f"\n--- Benchmark Complete. Results saved to '{output_filename}' ---")
    print(results_df.to_markdown(index=False))

if __name__ == "__main__":
    main()
