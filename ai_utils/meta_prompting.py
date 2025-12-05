<parameter name="language">python" title="Ollama Small Model Prompt Optimizer Pipeline" version_uuid="b692b4cc-4b19-4642-b82a-756f02e085ff">
"""
Ollama Pipeline for Small Model Prompt Optimization

This pipeline:
1. Uses a larger model to generate optimized prompts via the meta-prompt
2. Tests the generated prompt on a small model
3. Compares results and provides metrics
4. Iteratively refines if needed

Requirements:
    pip install ollama requests
"""

import ollama
import json
import time
from typing import Dict, List, Tuple

# Meta-prompt for generating small model optimized prompts
META_PROMPT = """# Meta-Prompt: Generating Prompts for Small Language Models

You are a prompt engineering assistant specialized in creating prompts optimized for small language models (models with limited parameters, context windows, and computational resources).

## Core Principles

When generating prompts for small models, follow these principles:

1. **Extreme Clarity and Specificity** - Use simple, direct language, avoid ambiguity
2. **Minimize Token Usage** - Keep prompts concise while maintaining clarity
3. **Structured Output Requirements** - Always specify the exact format
4. **Single-Task Focus** - One clear task per prompt
5. **Explicit Constraints** - Set clear length limits and boundaries

## Prompt Template Structure

[TASK] (clear, specific instruction)
[INPUT] (the data/question to process)
[CONSTRAINTS] (format, length, scope)
[OUTPUT FORMAT] (explicit structure)

## Your Task

Generate an optimized prompt for a small language model based on the user's request. Provide:
1. The optimized prompt (ready to use)
2. Estimated token count
3. Why it's optimized (2-3 points)

User Request: {user_request}

Respond in this JSON format:
{{
    "optimized_prompt": "the prompt text",
    "token_estimate": number,
    "optimization_notes": ["reason 1", "reason 2", "reason 3"]
}}
"""


class OllamaPromptOptimizer:
    """
    Pipeline for generating and testing small model optimized prompts.
    
    Steps:
    1. Initialize with model names
    2. Generate optimized prompt using larger model
    3. Test on small model
    4. Evaluate results
    """
    
    def __init__(self, generator_model: str = "llama3.2", small_model: str = "llama3.2"):
        """
        Initialize the optimizer pipeline.
        
        Args:
            generator_model: Model to generate optimized prompts (should be larger/better)
            small_model: Small model to test the prompts on
        """
        self.generator_model = generator_model
        self.small_model = small_model
        self.client = ollama
        
    def check_models_available(self) -> Tuple[bool, List[str]]:
        """
        Check if required models are available locally.
        
        Returns:
            Tuple of (all_available: bool, missing_models: List[str])
        """
        try:
            available_models = [m['name'] for m in self.client.list()['models']]
            missing = []
            
            if not any(self.generator_model in m for m in available_models):
                missing.append(self.generator_model)
            if not any(self.small_model in m for m in available_models):
                missing.append(self.small_model)
                
            return len(missing) == 0, missing
        except Exception as e:
            print(f"Error checking models: {e}")
            return False, []
    
    def generate_optimized_prompt(self, user_request: str) -> Dict:
        """
        Step 1: Use meta-prompt to generate an optimized prompt.
        
        Args:
            user_request: User's description of what they want the prompt to do
            
        Returns:
            Dictionary with optimized_prompt, token_estimate, and optimization_notes
        """
        print(f"\n{'='*60}")
        print("STEP 1: Generating Optimized Prompt")
        print(f"{'='*60}")
        print(f"Using model: {self.generator_model}")
        print(f"User request: {user_request}\n")
        
        # Format the meta-prompt with user's request
        full_prompt = META_PROMPT.format(user_request=user_request)
        
        # Generate using larger model
        start_time = time.time()
        response = self.client.generate(
            model=self.generator_model,
            prompt=full_prompt,
            options={
                "temperature": 0.3,  # Lower temperature for more consistent output
                "num_predict": 500
            }
        )
        generation_time = time.time() - start_time
        
        print(f"Generation time: {generation_time:.2f}s")
        
        # Parse JSON response
        try:
            # Try to find JSON in the response
            response_text = response['response']
            
            # Extract JSON if it's wrapped in markdown
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            print("\n✓ Successfully generated optimized prompt")
            print(f"\nOptimized Prompt:\n{'-'*60}")
            print(result['optimized_prompt'])
            print(f"{'-'*60}")
            print(f"\nToken Estimate: ~{result['token_estimate']} tokens")
            print("\nOptimization Notes:")
            for i, note in enumerate(result['optimization_notes'], 1):
                print(f"  {i}. {note}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"\n⚠ Warning: Could not parse JSON response. Using raw response.")
            print(f"Error: {e}")
            print(f"Response: {response['response'][:200]}...")
            
            # Fallback: return the response as-is
            return {
                "optimized_prompt": response['response'],
                "token_estimate": len(response['response'].split()),
                "optimization_notes": ["Generated but not in expected format"]
            }
    
    def test_on_small_model(self, optimized_prompt: str, test_input: str = None) -> Dict:
        """
        Step 2: Test the optimized prompt on the small model.
        
        Args:
            optimized_prompt: The prompt to test
            test_input: Optional test input to append to prompt
            
        Returns:
            Dictionary with response, time, and token count
        """
        print(f"\n{'='*60}")
        print("STEP 2: Testing on Small Model")
        print(f"{'='*60}")
        print(f"Using model: {self.small_model}\n")
        
        # Build final prompt
        final_prompt = optimized_prompt
        if test_input:
            final_prompt = f"{optimized_prompt}\n\n{test_input}"
            print(f"Test input: {test_input}\n")
        
        # Test on small model
        start_time = time.time()
        response = self.client.generate(
            model=self.small_model,
            prompt=final_prompt,
            options={
                "temperature": 0.7,
                "num_predict": 200
            }
        )
        inference_time = time.time() - start_time
        
        result = {
            "response": response['response'],
            "inference_time": inference_time,
            "prompt_tokens": response.get('prompt_eval_count', 0),
            "response_tokens": response.get('eval_count', 0),
            "total_tokens": response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
        }
        
        print(f"✓ Small model response generated")
        print(f"\nResponse:\n{'-'*60}")
        print(result['response'][:300] + ("..." if len(result['response']) > 300 else ""))
        print(f"{'-'*60}")
        print(f"\nInference time: {inference_time:.2f}s")
        print(f"Prompt tokens: {result['prompt_tokens']}")
        print(f"Response tokens: {result['response_tokens']}")
        print(f"Total tokens: {result['total_tokens']}")
        
        return result
    
    def compare_with_baseline(self, user_request: str, test_input: str = None) -> Dict:
        """
        Step 3: Compare optimized prompt vs baseline (user's original request).
        
        Args:
            user_request: Original user request (used as baseline)
            test_input: Test input for both prompts
            
        Returns:
            Comparison metrics
        """
        print(f"\n{'='*60}")
        print("STEP 3: Baseline Comparison")
        print(f"{'='*60}\n")
        
        # Test baseline (user's original request)
        baseline_prompt = user_request
        if test_input:
            baseline_prompt = f"{user_request}\n\n{test_input}"
        
        print("Testing baseline prompt (unoptimized)...")
        start_time = time.time()
        baseline_response = self.client.generate(
            model=self.small_model,
            prompt=baseline_prompt,
            options={"temperature": 0.7, "num_predict": 200}
        )
        baseline_time = time.time() - start_time
        
        print(f"✓ Baseline test complete ({baseline_time:.2f}s)")
        
        return {
            "baseline_time": baseline_time,
            "baseline_tokens": baseline_response.get('prompt_eval_count', 0),
            "baseline_response": baseline_response['response']
        }
    
    def run_pipeline(self, user_request: str, test_input: str = None, compare: bool = True):
        """
        Run the complete optimization pipeline.
        
        Steps:
        1. Check models are available
        2. Generate optimized prompt using meta-prompt
        3. Test optimized prompt on small model
        4. (Optional) Compare with baseline
        5. Display final summary
        
        Args:
            user_request: What the user wants the prompt to accomplish
            test_input: Optional test input to evaluate the prompt
            compare: Whether to compare with baseline
        """
        print("\n" + "="*60)
        print("OLLAMA SMALL MODEL PROMPT OPTIMIZER PIPELINE")
        print("="*60)
        
        # Check models
        available, missing = self.check_models_available()
        if not available:
            print(f"\n⚠ Error: Missing models: {missing}")
            print("Please install with: ollama pull <model_name>")
            return
        
        print(f"✓ Models available: {self.generator_model}, {self.small_model}")
        
        # Step 1: Generate optimized prompt
        optimization_result = self.generate_optimized_prompt(user_request)
        optimized_prompt = optimization_result['optimized_prompt']
        
        # Step 2: Test on small model
        test_result = self.test_on_small_model(optimized_prompt, test_input)
        
        # Step 3: Optional baseline comparison
        comparison = None
        if compare:
            comparison = self.compare_with_baseline(user_request, test_input)
        
        # Final Summary
        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}\n")
        
        print(f"Original Request Length: {len(user_request.split())} words")
        print(f"Optimized Prompt Length: {len(optimized_prompt.split())} words")
        print(f"Reduction: {len(user_request.split()) - len(optimized_prompt.split())} words")
        print(f"\nSmall Model Inference: {test_result['inference_time']:.2f}s")
        print(f"Tokens Used: {test_result['total_tokens']}")
        
        if comparison:
            print(f"\nBaseline Inference: {comparison['baseline_time']:.2f}s")
            time_diff = comparison['baseline_time'] - test_result['inference_time']
            print(f"Time Improvement: {time_diff:.2f}s ({time_diff/comparison['baseline_time']*100:.1f}%)")
            token_diff = comparison['baseline_tokens'] - test_result['prompt_tokens']
            print(f"Token Reduction: {token_diff} tokens")
        
        print("\n✓ Pipeline complete!")
        
        return {
            "optimized_prompt": optimized_prompt,
            "optimization_notes": optimization_result['optimization_notes'],
            "test_result": test_result,
            "comparison": comparison
        }


# Example usage and demonstrations
def main():
    """
    Main function demonstrating the pipeline with examples.
    """
    # Initialize optimizer
    optimizer = OllamaPromptOptimizer(
        generator_model="llama3.2",  # Use a capable model for generation
        small_model="llama3.2"        # Test on small/fast model
    )
    
    print("\n" + "🚀 "*30)
    print("Welcome to the Ollama Small Model Prompt Optimizer!")
    print("🚀 "*30 + "\n")
    
    # Example 1: Sentiment Classification
    print("\n" + "="*60)
    print("EXAMPLE 1: Sentiment Classification Task")
    print("="*60)
    
    user_request_1 = """
    I need to classify customer reviews as positive, negative, or neutral.
    Please analyze the sentiment and provide a classification.
    """
    
    test_input_1 = "Review: This product exceeded my expectations! Fast shipping too."
    
    optimizer.run_pipeline(
        user_request=user_request_1,
        test_input=test_input_1,
        compare=True
    )
    
    # Example 2: Data Extraction
    print("\n\n" + "="*60)
    print("EXAMPLE 2: Email Extraction Task")
    print("="*60)
    
    user_request_2 = """
    Extract email addresses from text. I need you to find all the email
    addresses in the provided text and list them out clearly.
    """
    
    test_input_2 = "Contact us at support@example.com or sales@company.org for inquiries."
    
    optimizer.run_pipeline(
        user_request=user_request_2,
        test_input=test_input_2,
        compare=True
    )
    
    # Example 3: Summarization
    print("\n\n" + "="*60)
    print("EXAMPLE 3: Text Summarization Task")
    print("="*60)
    
    user_request_3 = """
    Please summarize the following text in a concise way that captures
    the main points. Keep it brief but informative.
    """
    
    test_input_3 = """
    Artificial intelligence has made remarkable progress in recent years.
    Machine learning models can now perform complex tasks like image recognition,
    natural language processing, and game playing at or above human level.
    However, challenges remain in areas like reasoning, common sense understanding,
    and energy efficiency.
    """
    
    optimizer.run_pipeline(
        user_request=user_request_3,
        test_input=test_input_3,
        compare=True
    )


if __name__ == "__main__":
    # Run the demonstrations
    main()
    
    # Interactive mode
    print("\n\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("\nYou can now test your own prompts!")
    print("Enter your prompt request (or 'quit' to exit):\n")
    
    optimizer = OllamaPromptOptimizer()
    
    while True:
        user_input = input("\nYour request: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! 👋")
            break
        
        if not user_input:
            continue
        
        test_data = input("Test input (optional, press Enter to skip): ").strip()
        test_data = test_data if test_data else None
        
        optimizer.run_pipeline(
            user_request=user_input,
            test_input=test_data,
            compare=True
        )