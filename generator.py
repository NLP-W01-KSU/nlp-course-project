import os
import time
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class MultiGroqGenerator:
    def __init__(self):
        self.providers = self._initialize_groq_providers()
        self.models = self._get_best_models()
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def _initialize_groq_providers(self):
        """Initialize multiple Groq API providers with different keys"""
        providers = []
        
        # Get all Groq API keys from environment
        groq_keys = [
            os.getenv("GROQ_API_KEY_1"),
            os.getenv("GROQ_API_KEY_2"), 
            #os.getenv("GROQ_API_KEY_3")  # Add more as needed
        ]
        
        # Filter out None values and create providers
        for i, key in enumerate(groq_keys):
            if key and key.strip():
                providers.append({
                    'name': f'Groq-{i+1}',
                    'client': OpenAI(
                        api_key=key.strip(),
                        base_url="https://api.groq.com/openai/v1"
                    ),
                    'weight': 10,  # Start with equal weight
                    'fail_count': 0,
                    'last_used': 0
                })
        
        if not providers:
            raise ValueError("No Groq API keys found. Please set GROQ_API_KEY_1, GROQ_API_KEY_2, etc.")
            
        print(f"✅ Initialized {len(providers)} Groq providers")
        return providers
    
    def _get_best_models(self):
        """Select only the 2-3 best models for educational content"""
        return [
            # Best overall for educational content
            {
                'id': 'llama-3.3-70b-versatile',
                'name': 'Llama 3.3 70B',
                'weight': 10,  # Highest priority
                'max_tokens': 12000,
                'description': 'Most capable model - best for complex explanations'
            },
            # Good balance of speed and quality
            {
                'id': 'meta-llama/llama-4-maverick-17b-128e-instruct',
                'name': 'Llama 4 Maverick 17B', 
                'weight': 8,
                'max_tokens': 128000,
                'description': 'Excellent for detailed educational content'
            },
            # Fast and reliable fallback
            {
                'id': 'llama-3.1-8b-instant',
                'name': 'Llama 3.1 8B Instant',
                'weight': 6,
                'max_tokens': 6000,
                'description': 'Very fast for quick explanations'
            }
        ]
    
    def _select_provider(self):
        """Select provider based on weight and fail history"""
        # Filter out recently failed providers
        available_providers = [
            p for p in self.providers 
            if p['fail_count'] < 3 and (time.time() - p['last_used']) > 30
        ]
        
        if not available_providers:
            # If all are failing, reset and use any
            available_providers = self.providers
            for p in available_providers:
                p['fail_count'] = max(0, p['fail_count'] - 1)  # Gradual recovery
        
        weights = [p['weight'] for p in available_providers]
        selected = random.choices(available_providers, weights=weights, k=1)[0]
        selected['last_used'] = time.time()
        return selected
    
    def _select_model(self, prompt_length: int):
        """Select appropriate model - simpler logic with fewer models"""
        # With only 3 models, we can use simpler logic
        if prompt_length > 3000:
            # Use the most capable model for long prompts
            return self.models[0]  # Llama 3.3 70B
        elif prompt_length > 1500:
            # Use balanced model for medium prompts
            return self.models[1]  # Llama 4 Maverick
        else:
            # Use fast model for short prompts
            return self.models[2]  # Llama 3.1 8B Instant
    
    def generate(self, prompt: str) -> str:
        """Generate content with automatic failover between Groq keys"""
        last_error = None
        prompt_length = len(prompt)
        
        for attempt in range(self.max_retries + 1):
            provider = self._select_provider()
            model = self._select_model(prompt_length)
            
            try:
                print(f"🔄 Attempt {attempt + 1} with {provider['name']} using {model['name']}...")
                
                result = self._call_groq(provider, model, prompt)
                
                if result and not result.startswith("[Error"):
                    print(f"✅ Success with {provider['name']} + {model['name']}")
                    # Reward successful provider
                    provider['weight'] = min(20, provider['weight'] + 1)
                    provider['fail_count'] = max(0, provider['fail_count'] - 1)
                    return result
                    
            except Exception as e:
                last_error = str(e)
                print(f"❌ {provider['name']} + {model['name']} failed: {last_error}")
                
                # Penalize failed provider
                provider['weight'] = max(1, provider['weight'] - 2)
                provider['fail_count'] += 1
                
                # Wait before retry
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⏰ Waiting {delay}s before retry...")
                    time.sleep(delay)
        
        # All providers failed
        return self._get_user_friendly_error(last_error)
    
    def _call_groq(self, provider, model, prompt: str) -> str:
        """Call Groq API with specific provider and model"""
        try:
            response = provider['client'].chat.completions.create(
                model=model['id'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=min(4000, model['max_tokens'] - 1000),  # Leave room for response
                top_p=0.9
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg or "429" in error_msg:
                return f"[RateLimit] {provider['name']} rate limit exceeded"
            elif "quota" in error_msg:
                return f"[Quota] {provider['name']} quota exceeded"
            elif "authentication" in error_msg or "401" in error_msg or "403" in error_msg:
                return f"[Auth] {provider['name']} authentication failed"
            else:
                return f"[Error] {provider['name']}: {str(e)}"
    
    def _get_user_friendly_error(self, technical_error: str) -> str:
        """Convert technical errors to user-friendly messages"""
        error_lower = technical_error.lower()
        
        if "rate limit" in error_lower or "429" in error_lower:
            return """
🚫 **Service Temporarily Limited**

We're experiencing high demand right now across our AI services.

**What you can do:**
- Wait 10-15 minutes and try again
- We're automatically trying different services in the background
- This usually resolves quickly

Thank you for your patience! 🙏
"""
        elif "quota" in error_lower:
            return """
📊 **Daily Limits Reached**

We've used all our free AI credits for today.

**Next steps:**
- Try again tomorrow - limits reset daily
- We're working on adding more capacity

Thank you for helping with our research! ✨
"""
        else:
            return """
❌ **Temporary Service Issue**

We're having trouble connecting to our AI services.

**Please try:**
- Refreshing the page and trying again in a few minutes
- If this continues, we may be doing maintenance

We'll be back online shortly! ⚡
"""

    def get_service_status(self) -> dict:
        """Get current status of all providers"""
        status = {
            'total_providers': len(self.providers),
            'healthy_providers': len([p for p in self.providers if p['fail_count'] < 2]),
            'providers': [],
            'models': [m['name'] for m in self.models]  # Just show names
        }
        
        for provider in self.providers:
            if provider['fail_count'] >= 3:
                status_text = "🔴 Limited"
            elif provider['fail_count'] >= 1:
                status_text = "🟡 Slow"
            else:
                status_text = "🟢 Good"
                
            status['providers'].append({
                'name': provider['name'],
                'status': status_text,
                'failures': provider['fail_count']
            })
        
        return status


# Backward compatibility
class GroqGenerator(MultiGroqGenerator):
    """Legacy class for backward compatibility"""
    def __init__(self, model="llama-3.3-70b-versatile"):  # Default to best model
        super().__init__()

class HFGenerator:
    """Placeholder for future expansion"""
    pass

    