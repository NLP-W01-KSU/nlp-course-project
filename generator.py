import os
import time
import random
import requests
from openai import OpenAI
from typing import Dict, List

def get_groq_api_keys():
    """Get Groq API keys from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first (deployment)
        import streamlit as st
        if hasattr(st, 'secrets') and 'groq' in st.secrets:
            groq_secrets = st.secrets["groq"]
            # Get ALL API keys from secrets
            api_keys = [
                groq_secrets.get("api_key_1"),
                groq_secrets.get("api_key_2"),
                groq_secrets.get("api_key"),  
            ]
            # Filter out None values
            valid_keys = [key for key in api_keys if key and key.strip()]
            if valid_keys:
                print(f"✅ Found {len(valid_keys)} Groq API keys in Streamlit secrets")
                return valid_keys
    except (ImportError, AttributeError, KeyError):
        pass
    
    # Fallback to environment variables (local development)
    groq_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY"),  # Fallback
    ]
    
    # Filter out None values
    valid_keys = [key for key in groq_keys if key and key.strip()]
    if valid_keys:
        print(f"✅ Found {len(valid_keys)} Groq API keys in environment")
        return valid_keys
    
    print("❌ No Groq API keys found")
    return []

def get_ollama_url():
    """Get Ollama URL from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first (deployment)
        import streamlit as st
        if hasattr(st, 'secrets') and 'ollama' in st.secrets:
            url = st.secrets["ollama"].get("url")
            if url:
                return url
    except (ImportError, AttributeError, KeyError):
        pass
    
    # Fallback to environment variable (local development)
    return os.getenv("MODEL_URL")

class MultiGroqGenerator:
    def __init__(self):
        self.providers = self._initialize_groq_providers()
        self.models = self._get_best_models()
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def _initialize_groq_providers(self):
        """Initialize multiple Groq API providers with different keys"""
        providers = []
        
        # Get all Groq API keys
        groq_keys = get_groq_api_keys()
        
        # Filter out None values and create providers
        for i, key in enumerate(groq_keys):
            if key and key.strip():
                providers.append({
                    'name': f'Groq-{i+1}',
                    'client': OpenAI(
                        api_key=key.strip(),
                        base_url="https://api.groq.com/openai/v1"
                    ),
                    'weight': 10,
                    'fail_count': 0,
                    'last_used': 0
                })
        
        if not providers:
            raise ValueError("No Groq API keys found. Please set GROQ_API_KEY in environment variables or Streamlit secrets.")
            
        print(f"✅ Initialized {len(providers)} Groq providers")
        return providers
    
    def _get_best_models(self):
        """Select optimal models for educational content"""
        return [
            {
                'id': 'llama-3.3-70b-versatile',
                'name': 'Llama 3.3 70B',
                'weight': 10,
                'max_tokens': 32768,
                'description': 'Best for complex explanations'
            },
            {
                'id': 'meta-llama/llama-4-maverick-17b-128e-instruct', 
                'name': 'Llama 4 Maverick 17B',
                'weight': 9,
                'max_tokens': 128000,
                'description': 'Large context for big documents'
            },
            {
                'id': 'llama-3.1-8b-instant',
                'name': 'Llama 3.1 8B Instant',
                'weight': 8,
                'max_tokens': 32768,
                'description': 'Fast for most content'
            },
        ]
    
    def _select_provider(self):
        """Select provider based on weight and fail history"""
        available_providers = [
            p for p in self.providers 
            if p['fail_count'] < 3 and (time.time() - p['last_used']) > 30
        ]
        
        if not available_providers:
            available_providers = self.providers
            for p in available_providers:
                p['fail_count'] = max(0, p['fail_count'] - 1)
        
        weights = [p['weight'] for p in available_providers]
        selected = random.choices(available_providers, weights=weights, k=1)[0]
        selected['last_used'] = time.time()
        return selected
    
    def _select_model(self, prompt_length: int):
        """Select optimal model based on prompt size"""
        approx_tokens = prompt_length // 4
        
        if approx_tokens > 20000:
            return self.models[1]  # Maverick for huge docs
        elif approx_tokens > 10000:
            return self.models[1]  # Maverick for large docs
        elif approx_tokens > 6000:
            return self.models[0]  # 70B for medium-large
        elif approx_tokens > 3000:
            return self.models[0]  # 70B for quality
        else:
            return self.models[2]  # 8B for speed
    
    def generate(self, prompt: str) -> str:
        """Generate content with automatic failover"""
        last_error = None
        prompt_length = len(prompt)
        
        for attempt in range(self.max_retries + 1):
            provider = self._select_provider()
            model = self._select_model(prompt_length)
            
            try:
                print(f"🔄 Attempt {attempt + 1} with {provider['name']} using {model['name']}...")
                
                result = self._call_groq(provider, model, prompt)
                
                if result and not result.startswith(("[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "[ModelNotFound]")):
                    print(f"✅ Success with {provider['name']} + {model['name']}")
                    provider['weight'] = min(20, provider['weight'] + 1)
                    provider['fail_count'] = max(0, provider['fail_count'] - 1)
                    return result
                else:
                    print(f"❌ Provider returned: {result}")
                    if "[ModelNotFound]" in result:
                        continue
                    
            except Exception as e:
                last_error = str(e)
                print(f"❌ {provider['name']} + {model['name']} failed: {last_error}")
                provider['weight'] = max(1, provider['weight'] - 2)
                provider['fail_count'] += 1
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"⏰ Waiting {delay}s before retry...")
                    time.sleep(delay)
        
        return self._fallback_generate(prompt)
    
    def generate_large_content(self, prompt: str) -> str:
        """Handle large content generation for Groq - compatibility method"""
        print("🔷 Using Groq for large content generation...")
        
        # For Groq, we can handle large content directly due to large context windows
        # Just use the normal generate method with optimized model selection
        prompt_length = len(prompt)
        
        if prompt_length > 20000:  # Very large prompt
            print("📝 Large prompt detected, optimizing for Groq Maverick...")
            # Temporarily prioritize Maverick for large contexts
            original_models = self.models.copy()
            self.models = [self.models[1]]  # Maverick has 128K context
            try:
                result = self.generate(prompt)
                return result
            finally:
                self.models = original_models  # Restore original models
        else:
            # Use normal generation
            return self.generate(prompt)
    
    def _fallback_generate(self, prompt: str) -> str:
        """Fallback generation with simpler model selection"""
        print("🔄 Trying fallback generation...")
        
        fallback_models = [self.models[2], self.models[0]]
        
        for model in fallback_models:
            for provider in self.providers:
                try:
                    print(f"🔄 Fallback with {provider['name']} using {model['name']}...")
                    result = self._call_groq(provider, model, prompt)
                    
                    if result and not result.startswith(("[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "[ModelNotFound]")):
                        print(f"✅ Fallback success with {provider['name']} + {model['name']}")
                        return result
                except Exception as e:
                    print(f"❌ Fallback failed: {e}")
                    continue
        
        return self._get_user_friendly_error("All models failed")
    
    def _call_groq(self, provider, model, prompt: str) -> str:
        """Call Groq API with specific provider and model"""
        try:
            prompt_tokens_approx = len(prompt) // 4
            available_tokens = model['max_tokens'] - prompt_tokens_approx - 500
            max_response_tokens = max(1000, min(8000, available_tokens))
            
            response = provider['client'].chat.completions.create(
                model=model['id'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_response_tokens,
                top_p=0.9
            )
            
            if (response and response.choices and len(response.choices) > 0 and 
                response.choices[0].message and response.choices[0].message.content):
                
                content = response.choices[0].message.content.strip()
                return content if content else "[Empty] No content generated"
            else:
                return "[Empty] Invalid response structure"
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg or "429" in error_msg:
                return f"[RateLimit] {provider['name']} rate limit exceeded"
            elif "quota" in error_msg:
                return f"[Quota] {provider['name']} quota exceeded"
            elif "authentication" in error_msg:
                return f"[Auth] {provider['name']} authentication failed"
            elif "context length" in error_msg:
                return f"[Length] {provider['name']} content too long"
            elif "model not found" in error_msg:
                return f"[ModelNotFound] {provider['name']}: {str(e)}"
            else:
                return f"[Error] {provider['name']}: {str(e)}"
    
    def _get_user_friendly_error(self, technical_error: str) -> str:
        """Convert technical errors to user-friendly messages"""
        error_lower = technical_error.lower()
        
        if "rate limit" in error_lower:
            return "🚫 **Service Busy** - Please wait a few minutes and try again"
        elif "quota" in error_lower:
            return "📊 **Daily Limit Reached** - Try again tomorrow"
        elif "length" in error_lower:
            return "📝 **Content Too Large** - Please break into smaller sections"
        else:
            return "❌ **Temporary Issue** - Please try again shortly"

    def get_service_status(self) -> dict:
        """Get current status of all providers"""
        status = {
            'total_providers': len(self.providers),
            'healthy_providers': len([p for p in self.providers if p['fail_count'] < 2]),
            'providers': [],
            'models': [m['name'] for m in self.models]
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


class HFGenerator:
    """Phi-3 Generator with Auto-Pull, Smart Chunking, and Context Preservation"""
    
    def __init__(self, base_url: str = None):
        # Use environment variable or Streamlit secret as default
        self.base_url = base_url or get_ollama_url()
        self.model = "phi3:mini"
        self.current_requests = 0
        self.max_concurrent = 2
        self.model_available = False
        
        # Only try to connect if base_url is provided
        if self.base_url:
            self._ensure_model_available()
        else:
            print("⚠️ Ollama URL not configured - Phi-3 will not be available")
    
    def _ensure_model_available(self):
        """Check if model is available and pull if needed"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                self.model_available = any(model['name'] == self.model for model in models)
                
                if not self.model_available:
                    print(f"🔄 Model {self.model} not found, pulling...")
                    self._pull_model()
                else:
                    print(f"✅ Model {self.model} is available")
            else:
                print(f"❌ Could not check models: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking models: {e}")
    
    def _pull_model(self):
        """Pull the Phi-3 model if not available"""
        try:
            print(f"📥 Pulling {self.model}... This may take a few minutes.")
            
            payload = {"name": self.model}
            response = requests.post(
                f"{self.base_url}/api/pull", 
                json=payload, 
                timeout=300  # 5 minute timeout for pull
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully pulled {self.model}")
                self.model_available = True
                return True
            else:
                print(f"❌ Failed to pull model: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling model: {e}")
            return False
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def _chunk_content(self, content: str, max_tokens: int = 2500) -> list:
        """Split large content into manageable chunks"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            para_tokens = self._estimate_tokens(paragraph)
            
            if para_tokens > max_tokens:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sent_tokens = self._estimate_tokens(sentence)
                    if current_tokens + sent_tokens > max_tokens:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                        current_tokens = sent_tokens
                    else:
                        current_chunk += " " + sentence
                        current_tokens += sent_tokens
            else:
                if current_tokens + para_tokens > max_tokens:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                    current_tokens = para_tokens
                else:
                    current_chunk += "\n\n" + paragraph
                    current_tokens += para_tokens
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _create_context_summary(self, previous_chunks: list) -> str:
        """Create a context summary from previous chunks"""
        if not previous_chunks:
            return ""
        
        context_prompt = f"""
        Here's a summary of previous sections:
        {chr(10).join(previous_chunks)}
        
        Provide a brief summary (2-3 sentences) of key points to help understand the next section.
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": context_prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "num_predict": 200
                }
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()['message']['content'].strip()
            return f"Previous sections covered: {', '.join(previous_chunks[:2])}..."
        except Exception:
            return f"Context from {len(previous_chunks)} previous sections"
    
    def _create_chunk_summary(self, content: str) -> str:
        """Create a very brief summary of a chunk's content"""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": f"Summarize key points in 1-2 sentences: {content}"}],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "num_predict": 100
                }
            }
            
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=20)
            if response.status_code == 200:
                return response.json()['message']['content'].strip()
            return content[:100] + "..."
        except:
            return content[:100] + "..."
    
    def _call_ollama_with_retry(self, payload: dict, max_retries: int = 2) -> Dict:
        """Call Ollama API with auto-pull retry"""
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 404 and "not found" in response.text.lower():
                    print(f"🔄 Model not found, attempting to pull... (attempt {attempt + 1})")
                    if self._pull_model():
                        continue  # Retry after successful pull
                    else:
                        return {"success": False, "error": "Failed to pull model"}
                else:
                    return {"success": False, "error": f"API error {response.status_code}: {response.text}"}
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    print(f"⏰ Timeout, retrying... (attempt {attempt + 1})")
                    time.sleep(2)
                else:
                    return {"success": False, "error": "Request timeout"}
            except Exception as e:
                return {"success": False, "error": f"Connection failed: {str(e)}"}
        
        return {"success": False, "error": "All retries failed"}
    
    def generate(self, prompt: str, user_type: str = "student", 
                 academic_level: str = "undergraduate", 
                 content_type: str = "simplified_explanation") -> str:
        """Generate educational content with auto-pull and smart features - FIXED to return string"""
        
        # Check if Ollama is configured
        if not self.base_url:
            return "❌ Phi-3 Error: Ollama URL not configured. Please set MODEL_URL environment variable or add to Streamlit secrets."
        
        # Check if we need to pull model first
        if not self.model_available:
            print("🔄 Model not available, pulling before generation...")
            if not self._pull_model():
                return f"❌ Phi-3 Error: Phi-3 model is not available and failed to pull. Please check the Ollama server."
        
        estimated_tokens = self._estimate_tokens(prompt)
        
        # Auto-detect large documents and use chunking
        if estimated_tokens > 3000:
            result = self.generate_large_content_with_context(prompt, user_type, academic_level, content_type)
            if isinstance(result, dict):
                return result.get("content", f"❌ Phi-3 Error: {result.get('error', 'Unknown error')}")
            return result
        
        # Queue management
        if self.current_requests >= self.max_concurrent:
            queue_position = self.current_requests - self.max_concurrent + 1
            estimated_wait = queue_position * 7
            return f"❌ Phi-3 Error: Service busy. You're #{queue_position} in queue (~{estimated_wait}s)"
        
        self.current_requests += 1
        try:
            # Use the prompt directly without adding instructional wrapper
            # The prompts from tutor_flow and student_flow now tell it to generate content directly
            
            # FIXED: Increased token allocation for complete responses
            if estimated_tokens > 2000:
                max_output_tokens = 2000  # Increased from 500
            elif estimated_tokens > 1000:
                max_output_tokens = 2500  # Increased from 800
            else:
                max_output_tokens = 3000  # Increased from 1000
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": max_output_tokens
                }
            }
            
            start_time = time.time()
            result = self._call_ollama_with_retry(payload)
            inference_time = time.time() - start_time
            
            if result["success"]:
                data = result["data"]
                content = data['message']['content'].strip()
                
                # Check if content was cut off and retry with more tokens if needed
                if self._is_content_cut_off(content):
                    print("⚠️ Content appears cut off, retrying with more tokens...")
                    payload["options"]["num_predict"] = 4000  # Max tokens for Phi-3
                    retry_result = self._call_ollama_with_retry(payload)
                    
                    if retry_result["success"]:
                        data = retry_result["data"]
                        content = data['message']['content'].strip()
                
                return content
            else:
                return f"❌ Phi-3 Error: {result['error']}"
                
        except Exception as e:
            return f"❌ Phi-3 Error: {str(e)}"
        finally:
            self.current_requests -= 1

    def _is_content_cut_off(self, content: str) -> bool:
        """Check if content appears to be cut off mid-sentence"""
        if not content or len(content.strip()) < 100:
            return True
        
        # Check if it ends with proper punctuation
        if content.strip().endswith(('.', '!', '?', '."', '!"', '?"')):
            return False
        
        # Check if it ends with incomplete sentence markers
        if any(content.strip().endswith(marker) for marker in [',', ';', ':', '-', '–', '—']):
            return True
        
        # Check if it ends with an incomplete word or thought
        last_paragraph = content.strip().split('\n')[-1]
        if len(last_paragraph.split()) < 5:  # Very short last paragraph
            return True
        
        return False
    
    def generate_large_content_with_context(self, prompt: str, user_type: str = "student", 
                                          academic_level: str = "undergraduate", 
                                          content_type: str = "simplified_explanation") -> str:
        """Handle large documents with context preservation - FIXED to return string"""
        
        estimated_tokens = self._estimate_tokens(prompt)
        
        if estimated_tokens <= 3000:
            return self.generate(prompt, user_type, academic_level, content_type)
        
        chunks = self._chunk_content(prompt, max_tokens=2500)
        
        if len(chunks) > 6:
            return f"❌ Phi-3 Error: Document too large ({estimated_tokens} tokens, {len(chunks)} chunks). Please use Groq or break into smaller sections."
        
        all_results = []
        previous_summaries = []
        
        for i, chunk in enumerate(chunks):
            print(f"🔄 Processing chunk {i+1}/{len(chunks)} with context...")
            
            context_summary = self._create_context_summary(previous_summaries)
            
            if context_summary:
                chunk_prompt = f"""Part {i+1} of {len(chunks)} - Building on previous context:

**PREVIOUS CONTEXT:**
{context_summary}

**CURRENT SECTION:**
{chunk}

Analyze this section while connecting to the overall context."""
            else:
                chunk_prompt = f"""Part {i+1} of {len(chunks)}:

**CONTENT:**
{chunk}

Please analyze this section."""
            
            chunk_result = self.generate(chunk_prompt, user_type, academic_level, content_type)
            
            if "❌ Phi-3 Error:" not in chunk_result:
                chunk_summary = self._create_chunk_summary(chunk_result)
                previous_summaries.append(chunk_summary)
                
                all_results.append({
                    "chunk_number": i+1,
                    "content": chunk_result,
                    "context_used": bool(context_summary)
                })
            else:
                return f"❌ Phi-3 Error: Failed to process chunk {i+1}: {chunk_result}"
            
            if i < len(chunks) - 1:
                time.sleep(1)
        
        # Combine results
        combined_content = "\n\n".join([f"## Part {r['chunk_number']}\n{r['content']}" for r in all_results])
        
        return combined_content
    
    def health_check(self) -> Dict:
        """Comprehensive health check"""
        if not self.base_url:
            return {
                "server_healthy": False,
                "model_available": False,
                "error": "Ollama URL not configured"
            }
            
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_available = any(model['name'] == self.model for model in models)
                
                return {
                    "server_healthy": True,
                    "model_available": model_available,
                    "available_models": [model['name'] for model in models],
                    "model_required": self.model
                }
            else:
                return {
                    "server_healthy": False,
                    "model_available": False,
                    "error": f"Server returned {response.status_code}"
                }
        except Exception as e:
            return {
                "server_healthy": False,
                "model_available": False,
                "error": str(e)
            }
    
    def get_available_models(self):
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return [model['name'] for model in response.json().get('models', [])]
            return []
        except:
            return []
    
    def get_queue_status(self):
        """Get current queue status"""
        return {
            "current_requests": self.current_requests,
            "max_concurrent": self.max_concurrent,
            "available_slots": max(0, self.max_concurrent - self.current_requests)
        }


# Backward compatibility
class GroqGenerator(MultiGroqGenerator):
    def __init__(self, model="llama-3.3-70b-versatile"):
        super().__init__()


class ModelManager:
    """Unified model manager that handles both Groq and Phi-3 models"""
    
    def __init__(self):
        self.groq_generator = MultiGroqGenerator()
        self.phi3_generator = HFGenerator()
    
    def generate(self, prompt: str, model_choice: str = "phi3", **kwargs) -> str:
        """Generate content using selected model"""
        print(f"🎯 Using model: {model_choice}")
        
        if model_choice == "phi3":
            # Handle Phi-3 generation - FIXED: Now returns string directly
            user_type = kwargs.get('user_type', 'student')
            academic_level = kwargs.get('student_level', 'undergraduate')
            content_type = kwargs.get('content_type', 'simplified_explanation')
            
            result = self.phi3_generator.generate(prompt, user_type, academic_level, content_type)
            return result
        else:
            # Use Groq for comparison - check if this is a large content request
            is_large_content = len(prompt) > 8000  # You can adjust this threshold
            
            if is_large_content:
                return self.groq_generator.generate_large_content(prompt)
            else:
                return self.groq_generator.generate(prompt)
    
    def get_service_status(self) -> dict:
        """Get clean research-focused status"""
        groq_status = self.groq_generator.get_service_status()
        phi3_health = self.phi3_generator.health_check()
        
        # Clean Groq status - remove model names, focus on providers
        clean_groq_status = {
            'healthy_providers': groq_status['healthy_providers'],
            'total_providers': groq_status['total_providers'],
            'providers': [
                {
                    'name': provider['name'],
                    'failures': provider['failures']
                }
                for provider in groq_status['providers']
            ]
        }
        
        # Enhanced Phi-3 status
        enhanced_phi3_status = {
            'server_healthy': phi3_health['server_healthy'],
            'model_available': phi3_health['model_available'],
            'available_models': phi3_health['available_models'],
            'model_required': phi3_health['model_required']
        }
        
        return {
            "groq": clean_groq_status,
            "phi3": enhanced_phi3_status
        }


# Global model manager instance
model_manager = ModelManager()


# Setup function for your Streamlit app
def setup_generators():
    """Setup both generators with health checks"""
    print("🔧 Setting up generators...")
    
    groq_generator = MultiGroqGenerator()
    
    phi3_generator = HFGenerator()
    phi3_health = phi3_generator.health_check()
    
    print(f"🏥 Phi-3 Health: {phi3_health}")
    
    if not phi3_health["server_healthy"]:
        print("❌ Phi-3 server is not accessible")
    elif not phi3_health["model_available"]:
        print("🔄 Phi-3 model needs to be pulled on first use")
    
    return {
        "groq": groq_generator,
        "phi3": phi3_generator
    }


# Test function
def test_generators():
    """Test both generators"""
    print("🧪 Testing Generators...")
    
    generators = setup_generators()
    
    # Test Groq
    print("\n🔷 Testing Groq...")
    groq_result = generators["groq"].generate("Explain photosynthesis briefly")
    if not groq_result.startswith("["):
        print("✅ Groq working")
    else:
        print("❌ Groq failed:", groq_result)
    
    # Test Phi-3
    print("\n🔶 Testing Phi-3...")
    phi3_result = generators["phi3"].generate("Explain photosynthesis briefly")
    if "❌ Phi-3 Error:" not in phi3_result:
        print("✅ Phi-3 working")
    else:
        print("❌ Phi-3 failed:", phi3_result)
    
    # Test health
    print("\n🏥 Health Check:")
    print(f"Groq providers: {len(generators['groq'].providers)}")
    print(f"Phi-3 healthy: {generators['phi3'].health_check()}")


if __name__ == "__main__":
    test_generators()

# import os
# import time
# import random
# import requests
# from openai import OpenAI
# from dotenv import load_dotenv
# from typing import Dict, List

# # Load environment variables once at module level
# load_dotenv()

# class MultiGroqGenerator:
#     def __init__(self):
#         self.providers = self._initialize_groq_providers()
#         self.models = self._get_best_models()
#         self.max_retries = 3
#         self.retry_delay = 2  # seconds
        
#     def _initialize_groq_providers(self):
#         """Initialize multiple Groq API providers with different keys"""
#         providers = []
        
#         # Get all Groq API keys from environment
#         groq_keys = [
#             os.getenv("GROQ_API_KEY_1"),
#             os.getenv("GROQ_API_KEY_2"), 
#         ]
        
#         # Filter out None values and create providers
#         for i, key in enumerate(groq_keys):
#             if key and key.strip():
#                 providers.append({
#                     'name': f'Groq-{i+1}',
#                     'client': OpenAI(
#                         api_key=key.strip(),
#                         base_url="https://api.groq.com/openai/v1"
#                     ),
#                     'weight': 10,
#                     'fail_count': 0,
#                     'last_used': 0
#                 })
        
#         if not providers:
#             raise ValueError("No Groq API keys found. Please set GROQ_API_KEY_1, GROQ_API_KEY_2, etc.")
            
#         print(f"✅ Initialized {len(providers)} Groq providers")
#         return providers
    
#     def _get_best_models(self):
#         """Select optimal models for educational content"""
#         return [
#             {
#                 'id': 'llama-3.3-70b-versatile',
#                 'name': 'Llama 3.3 70B',
#                 'weight': 10,
#                 'max_tokens': 32768,
#                 'description': 'Best for complex explanations'
#             },
#             {
#                 'id': 'meta-llama/llama-4-maverick-17b-128e-instruct', 
#                 'name': 'Llama 4 Maverick 17B',
#                 'weight': 9,
#                 'max_tokens': 128000,
#                 'description': 'Large context for big documents'
#             },
#             {
#                 'id': 'llama-3.1-8b-instant',
#                 'name': 'Llama 3.1 8B Instant',
#                 'weight': 8,
#                 'max_tokens': 32768,
#                 'description': 'Fast for most content'
#             },
#         ]
    
#     def _select_provider(self):
#         """Select provider based on weight and fail history"""
#         available_providers = [
#             p for p in self.providers 
#             if p['fail_count'] < 3 and (time.time() - p['last_used']) > 30
#         ]
        
#         if not available_providers:
#             available_providers = self.providers
#             for p in available_providers:
#                 p['fail_count'] = max(0, p['fail_count'] - 1)
        
#         weights = [p['weight'] for p in available_providers]
#         selected = random.choices(available_providers, weights=weights, k=1)[0]
#         selected['last_used'] = time.time()
#         return selected
    
#     def _select_model(self, prompt_length: int):
#         """Select optimal model based on prompt size"""
#         approx_tokens = prompt_length // 4
        
#         if approx_tokens > 20000:
#             return self.models[1]  # Maverick for huge docs
#         elif approx_tokens > 10000:
#             return self.models[1]  # Maverick for large docs
#         elif approx_tokens > 6000:
#             return self.models[0]  # 70B for medium-large
#         elif approx_tokens > 3000:
#             return self.models[0]  # 70B for quality
#         else:
#             return self.models[2]  # 8B for speed
    
#     def generate(self, prompt: str) -> str:
#         """Generate content with automatic failover"""
#         last_error = None
#         prompt_length = len(prompt)
        
#         for attempt in range(self.max_retries + 1):
#             provider = self._select_provider()
#             model = self._select_model(prompt_length)
            
#             try:
#                 print(f"🔄 Attempt {attempt + 1} with {provider['name']} using {model['name']}...")
                
#                 result = self._call_groq(provider, model, prompt)
                
#                 if result and not result.startswith(("[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "[ModelNotFound]")):
#                     print(f"✅ Success with {provider['name']} + {model['name']}")
#                     provider['weight'] = min(20, provider['weight'] + 1)
#                     provider['fail_count'] = max(0, provider['fail_count'] - 1)
#                     return result
#                 else:
#                     print(f"❌ Provider returned: {result}")
#                     if "[ModelNotFound]" in result:
#                         continue
                    
#             except Exception as e:
#                 last_error = str(e)
#                 print(f"❌ {provider['name']} + {model['name']} failed: {last_error}")
#                 provider['weight'] = max(1, provider['weight'] - 2)
#                 provider['fail_count'] += 1
                
#                 if attempt < self.max_retries:
#                     delay = self.retry_delay * (2 ** attempt)
#                     print(f"⏰ Waiting {delay}s before retry...")
#                     time.sleep(delay)
        
#         return self._fallback_generate(prompt)
    
#     def generate_large_content(self, prompt: str) -> str:
#         """Handle large content generation for Groq - compatibility method"""
#         print("🔷 Using Groq for large content generation...")
        
#         # For Groq, we can handle large content directly due to large context windows
#         # Just use the normal generate method with optimized model selection
#         prompt_length = len(prompt)
        
#         if prompt_length > 20000:  # Very large prompt
#             print("📝 Large prompt detected, optimizing for Groq Maverick...")
#             # Temporarily prioritize Maverick for large contexts
#             original_models = self.models.copy()
#             self.models = [self.models[1]]  # Maverick has 128K context
#             try:
#                 result = self.generate(prompt)
#                 return result
#             finally:
#                 self.models = original_models  # Restore original models
#         else:
#             # Use normal generation
#             return self.generate(prompt)
    
#     def _fallback_generate(self, prompt: str) -> str:
#         """Fallback generation with simpler model selection"""
#         print("🔄 Trying fallback generation...")
        
#         fallback_models = [self.models[2], self.models[0]]
        
#         for model in fallback_models:
#             for provider in self.providers:
#                 try:
#                     print(f"🔄 Fallback with {provider['name']} using {model['name']}...")
#                     result = self._call_groq(provider, model, prompt)
                    
#                     if result and not result.startswith(("[Error", "[RateLimit]", "[Quota]", "[Auth]", "[Empty]", "[ModelNotFound]")):
#                         print(f"✅ Fallback success with {provider['name']} + {model['name']}")
#                         return result
#                 except Exception as e:
#                     print(f"❌ Fallback failed: {e}")
#                     continue
        
#         return self._get_user_friendly_error("All models failed")
    
#     def _call_groq(self, provider, model, prompt: str) -> str:
#         """Call Groq API with specific provider and model"""
#         try:
#             prompt_tokens_approx = len(prompt) // 4
#             available_tokens = model['max_tokens'] - prompt_tokens_approx - 500
#             max_response_tokens = max(1000, min(8000, available_tokens))
            
#             response = provider['client'].chat.completions.create(
#                 model=model['id'],
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.7,
#                 max_tokens=max_response_tokens,
#                 top_p=0.9
#             )
            
#             if (response and response.choices and len(response.choices) > 0 and 
#                 response.choices[0].message and response.choices[0].message.content):
                
#                 content = response.choices[0].message.content.strip()
#                 return content if content else "[Empty] No content generated"
#             else:
#                 return "[Empty] Invalid response structure"
                
#         except Exception as e:
#             error_msg = str(e).lower()
            
#             if "rate limit" in error_msg or "429" in error_msg:
#                 return f"[RateLimit] {provider['name']} rate limit exceeded"
#             elif "quota" in error_msg:
#                 return f"[Quota] {provider['name']} quota exceeded"
#             elif "authentication" in error_msg:
#                 return f"[Auth] {provider['name']} authentication failed"
#             elif "context length" in error_msg:
#                 return f"[Length] {provider['name']} content too long"
#             elif "model not found" in error_msg:
#                 return f"[ModelNotFound] {provider['name']}: {str(e)}"
#             else:
#                 return f"[Error] {provider['name']}: {str(e)}"
    
#     def _get_user_friendly_error(self, technical_error: str) -> str:
#         """Convert technical errors to user-friendly messages"""
#         error_lower = technical_error.lower()
        
#         if "rate limit" in error_lower:
#             return "🚫 **Service Busy** - Please wait a few minutes and try again"
#         elif "quota" in error_lower:
#             return "📊 **Daily Limit Reached** - Try again tomorrow"
#         elif "length" in error_lower:
#             return "📝 **Content Too Large** - Please break into smaller sections"
#         else:
#             return "❌ **Temporary Issue** - Please try again shortly"

#     def get_service_status(self) -> dict:
#         """Get current status of all providers"""
#         status = {
#             'total_providers': len(self.providers),
#             'healthy_providers': len([p for p in self.providers if p['fail_count'] < 2]),
#             'providers': [],
#             'models': [m['name'] for m in self.models]
#         }
        
#         for provider in self.providers:
#             if provider['fail_count'] >= 3:
#                 status_text = "🔴 Limited"
#             elif provider['fail_count'] >= 1:
#                 status_text = "🟡 Slow"
#             else:
#                 status_text = "🟢 Good"
                
#             status['providers'].append({
#                 'name': provider['name'],
#                 'status': status_text,
#                 'failures': provider['fail_count']
#             })
        
#         return status


# class HFGenerator:
#     """Phi-3 Generator with Auto-Pull, Smart Chunking, and Context Preservation"""
    
#     def __init__(self, base_url: str = None):
#         # Use environment variable as default if no base_url provided
#         self.base_url = base_url or os.getenv("MODEL_URL")
#         self.model = "phi3:mini"
#         self.current_requests = 0
#         self.max_concurrent = 2
#         self.model_available = False
#         self._ensure_model_available()
    
#     def _ensure_model_available(self):
#         """Check if model is available and pull if needed"""
#         try:
#             response = requests.get(f"{self.base_url}/api/tags", timeout=10)
#             if response.status_code == 200:
#                 models = response.json().get('models', [])
#                 self.model_available = any(model['name'] == self.model for model in models)
                
#                 if not self.model_available:
#                     print(f"🔄 Model {self.model} not found, pulling...")
#                     self._pull_model()
#                 else:
#                     print(f"✅ Model {self.model} is available")
#             else:
#                 print(f"❌ Could not check models: {response.status_code}")
#         except Exception as e:
#             print(f"❌ Error checking models: {e}")
    
#     def _pull_model(self):
#         """Pull the Phi-3 model if not available"""
#         try:
#             print(f"📥 Pulling {self.model}... This may take a few minutes.")
            
#             payload = {"name": self.model}
#             response = requests.post(
#                 f"{self.base_url}/api/pull", 
#                 json=payload, 
#                 timeout=300  # 5 minute timeout for pull
#             )
            
#             if response.status_code == 200:
#                 print(f"✅ Successfully pulled {self.model}")
#                 self.model_available = True
#                 return True
#             else:
#                 print(f"❌ Failed to pull model: {response.text}")
#                 return False
                
#         except Exception as e:
#             print(f"❌ Error pulling model: {e}")
#             return False
    
#     def _estimate_tokens(self, text: str) -> int:
#         """Rough token estimation"""
#         return len(text) // 4
    
#     def _chunk_content(self, content: str, max_tokens: int = 2500) -> list:
#         """Split large content into manageable chunks"""
#         paragraphs = content.split('\n\n')
#         chunks = []
#         current_chunk = ""
#         current_tokens = 0
        
#         for paragraph in paragraphs:
#             para_tokens = self._estimate_tokens(paragraph)
            
#             if para_tokens > max_tokens:
#                 sentences = paragraph.split('. ')
#                 for sentence in sentences:
#                     sent_tokens = self._estimate_tokens(sentence)
#                     if current_tokens + sent_tokens > max_tokens:
#                         if current_chunk:
#                             chunks.append(current_chunk.strip())
#                         current_chunk = sentence
#                         current_tokens = sent_tokens
#                     else:
#                         current_chunk += " " + sentence
#                         current_tokens += sent_tokens
#             else:
#                 if current_tokens + para_tokens > max_tokens:
#                     if current_chunk:
#                         chunks.append(current_chunk.strip())
#                     current_chunk = paragraph
#                     current_tokens = para_tokens
#                 else:
#                     current_chunk += "\n\n" + paragraph
#                     current_tokens += para_tokens
        
#         if current_chunk:
#             chunks.append(current_chunk.strip())
            
#         return chunks
    
#     def _create_context_summary(self, previous_chunks: list) -> str:
#         """Create a context summary from previous chunks"""
#         if not previous_chunks:
#             return ""
        
#         context_prompt = f"""
#         Here's a summary of previous sections:
#         {chr(10).join(previous_chunks)}
        
#         Provide a brief summary (2-3 sentences) of key points to help understand the next section.
#         """
        
#         try:
#             payload = {
#                 "model": self.model,
#                 "messages": [{"role": "user", "content": context_prompt}],
#                 "stream": False,
#                 "options": {
#                     "temperature": 0.3,
#                     "top_p": 0.8,
#                     "num_predict": 200
#                 }
#             }
            
#             response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
#             if response.status_code == 200:
#                 return response.json()['message']['content'].strip()
#             return f"Previous sections covered: {', '.join(previous_chunks[:2])}..."
#         except Exception:
#             return f"Context from {len(previous_chunks)} previous sections"
    
#     def _create_chunk_summary(self, content: str) -> str:
#         """Create a very brief summary of a chunk's content"""
#         try:
#             payload = {
#                 "model": self.model,
#                 "messages": [{"role": "user", "content": f"Summarize key points in 1-2 sentences: {content}"}],
#                 "stream": False,
#                 "options": {
#                     "temperature": 0.3,
#                     "top_p": 0.8,
#                     "num_predict": 100
#                 }
#             }
            
#             response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=20)
#             if response.status_code == 200:
#                 return response.json()['message']['content'].strip()
#             return content[:100] + "..."
#         except:
#             return content[:100] + "..."
    
#     def _call_ollama_with_retry(self, payload: dict, max_retries: int = 2) -> Dict:
#         """Call Ollama API with auto-pull retry"""
#         for attempt in range(max_retries + 1):
#             try:
#                 response = requests.post(
#                     f"{self.base_url}/api/chat",
#                     json=payload,
#                     timeout=60
#                 )
                
#                 if response.status_code == 200:
#                     return {"success": True, "data": response.json()}
#                 elif response.status_code == 404 and "not found" in response.text.lower():
#                     print(f"🔄 Model not found, attempting to pull... (attempt {attempt + 1})")
#                     if self._pull_model():
#                         continue  # Retry after successful pull
#                     else:
#                         return {"success": False, "error": "Failed to pull model"}
#                 else:
#                     return {"success": False, "error": f"API error {response.status_code}: {response.text}"}
                    
#             except requests.exceptions.Timeout:
#                 if attempt < max_retries:
#                     print(f"⏰ Timeout, retrying... (attempt {attempt + 1})")
#                     time.sleep(2)
#                 else:
#                     return {"success": False, "error": "Request timeout"}
#             except Exception as e:
#                 return {"success": False, "error": f"Connection failed: {str(e)}"}
        
#         return {"success": False, "error": "All retries failed"}
    
#     def generate(self, prompt: str, user_type: str = "student", 
#                  academic_level: str = "undergraduate", 
#                  content_type: str = "simplified_explanation") -> str:
#         """Generate educational content with auto-pull and smart features - FIXED to return string"""
        
#         # Check if we need to pull model first
#         if not self.model_available:
#             print("🔄 Model not available, pulling before generation...")
#             if not self._pull_model():
#                 return f"❌ Phi-3 Error: Phi-3 model is not available and failed to pull. Please check the Ollama server."
        
#         estimated_tokens = self._estimate_tokens(prompt)
        
#         # Auto-detect large documents and use chunking
#         if estimated_tokens > 3000:
#             result = self.generate_large_content_with_context(prompt, user_type, academic_level, content_type)
#             if isinstance(result, dict):
#                 return result.get("content", f"❌ Phi-3 Error: {result.get('error', 'Unknown error')}")
#             return result
        
#         # Queue management
#         if self.current_requests >= self.max_concurrent:
#             queue_position = self.current_requests - self.max_concurrent + 1
#             estimated_wait = queue_position * 7
#             return f"❌ Phi-3 Error: Service busy. You're #{queue_position} in queue (~{estimated_wait}s)"
        
#         self.current_requests += 1
#         try:
#             # Use the prompt directly without adding instructional wrapper
#             # The prompts from tutor_flow and student_flow now tell it to generate content directly
            
#             # FIXED: Increased token allocation for complete responses
#             if estimated_tokens > 2000:
#                 max_output_tokens = 2000  # Increased from 500
#             elif estimated_tokens > 1000:
#                 max_output_tokens = 2500  # Increased from 800
#             else:
#                 max_output_tokens = 3000  # Increased from 1000
            
#             payload = {
#                 "model": self.model,
#                 "messages": [{"role": "user", "content": prompt}],
#                 "stream": False,
#                 "options": {
#                     "temperature": 0.7,
#                     "top_p": 0.9,
#                     "num_predict": max_output_tokens
#                 }
#             }
            
#             start_time = time.time()
#             result = self._call_ollama_with_retry(payload)
#             inference_time = time.time() - start_time
            
#             if result["success"]:
#                 data = result["data"]
#                 content = data['message']['content'].strip()
                
#                 # Check if content was cut off and retry with more tokens if needed
#                 if self._is_content_cut_off(content):
#                     print("⚠️ Content appears cut off, retrying with more tokens...")
#                     payload["options"]["num_predict"] = 4000  # Max tokens for Phi-3
#                     retry_result = self._call_ollama_with_retry(payload)
                    
#                     if retry_result["success"]:
#                         data = retry_result["data"]
#                         content = data['message']['content'].strip()
                
#                 return content
#             else:
#                 return f"❌ Phi-3 Error: {result['error']}"
                
#         except Exception as e:
#             return f"❌ Phi-3 Error: {str(e)}"
#         finally:
#             self.current_requests -= 1

#     def _is_content_cut_off(self, content: str) -> bool:
#         """Check if content appears to be cut off mid-sentence"""
#         if not content or len(content.strip()) < 100:
#             return True
        
#         # Check if it ends with proper punctuation
#         if content.strip().endswith(('.', '!', '?', '."', '!"', '?"')):
#             return False
        
#         # Check if it ends with incomplete sentence markers
#         if any(content.strip().endswith(marker) for marker in [',', ';', ':', '-', '–', '—']):
#             return True
        
#         # Check if it ends with an incomplete word or thought
#         last_paragraph = content.strip().split('\n')[-1]
#         if len(last_paragraph.split()) < 5:  # Very short last paragraph
#             return True
        
#         return False
    
#     def generate_large_content_with_context(self, prompt: str, user_type: str = "student", 
#                                           academic_level: str = "undergraduate", 
#                                           content_type: str = "simplified_explanation") -> str:
#         """Handle large documents with context preservation - FIXED to return string"""
        
#         estimated_tokens = self._estimate_tokens(prompt)
        
#         if estimated_tokens <= 3000:
#             return self.generate(prompt, user_type, academic_level, content_type)
        
#         chunks = self._chunk_content(prompt, max_tokens=2500)
        
#         if len(chunks) > 6:
#             return f"❌ Phi-3 Error: Document too large ({estimated_tokens} tokens, {len(chunks)} chunks). Please use Groq or break into smaller sections."
        
#         all_results = []
#         previous_summaries = []
        
#         for i, chunk in enumerate(chunks):
#             print(f"🔄 Processing chunk {i+1}/{len(chunks)} with context...")
            
#             context_summary = self._create_context_summary(previous_summaries)
            
#             if context_summary:
#                 chunk_prompt = f"""Part {i+1} of {len(chunks)} - Building on previous context:

# **PREVIOUS CONTEXT:**
# {context_summary}

# **CURRENT SECTION:**
# {chunk}

# Analyze this section while connecting to the overall context."""
#             else:
#                 chunk_prompt = f"""Part {i+1} of {len(chunks)}:

# **CONTENT:**
# {chunk}

# Please analyze this section."""
            
#             chunk_result = self.generate(chunk_prompt, user_type, academic_level, content_type)
            
#             if "❌ Phi-3 Error:" not in chunk_result:
#                 chunk_summary = self._create_chunk_summary(chunk_result)
#                 previous_summaries.append(chunk_summary)
                
#                 all_results.append({
#                     "chunk_number": i+1,
#                     "content": chunk_result,
#                     "context_used": bool(context_summary)
#                 })
#             else:
#                 return f"❌ Phi-3 Error: Failed to process chunk {i+1}: {chunk_result}"
            
#             if i < len(chunks) - 1:
#                 time.sleep(1)
        
#         # Combine results
#         combined_content = "\n\n".join([f"## Part {r['chunk_number']}\n{r['content']}" for r in all_results])
        
#         return combined_content
    
#     def health_check(self) -> Dict:
#         """Comprehensive health check"""
#         try:
#             response = requests.get(f"{self.base_url}/api/tags", timeout=10)
#             if response.status_code == 200:
#                 models = response.json().get('models', [])
#                 model_available = any(model['name'] == self.model for model in models)
                
#                 return {
#                     "server_healthy": True,
#                     "model_available": model_available,
#                     "available_models": [model['name'] for model in models],
#                     "model_required": self.model
#                 }
#             else:
#                 return {
#                     "server_healthy": False,
#                     "model_available": False,
#                     "error": f"Server returned {response.status_code}"
#                 }
#         except Exception as e:
#             return {
#                 "server_healthy": False,
#                 "model_available": False,
#                 "error": str(e)
#             }
    
#     def get_available_models(self):
#         """Get list of available models"""
#         try:
#             response = requests.get(f"{self.base_url}/api/tags", timeout=10)
#             if response.status_code == 200:
#                 return [model['name'] for model in response.json().get('models', [])]
#             return []
#         except:
#             return []
    
#     def get_queue_status(self):
#         """Get current queue status"""
#         return {
#             "current_requests": self.current_requests,
#             "max_concurrent": self.max_concurrent,
#             "available_slots": max(0, self.max_concurrent - self.current_requests)
#         }


# # Backward compatibility
# class GroqGenerator(MultiGroqGenerator):
#     def __init__(self, model="llama-3.3-70b-versatile"):
#         super().__init__()


# class ModelManager:
#     """Unified model manager that handles both Groq and Phi-3 models"""
    
#     def __init__(self):
#         self.groq_generator = MultiGroqGenerator()
#         self.phi3_generator = HFGenerator()
    
#     def generate(self, prompt: str, model_choice: str = "phi3", **kwargs) -> str:
#         """Generate content using selected model"""
#         print(f"🎯 Using model: {model_choice}")
        
#         if model_choice == "phi3":
#             # Handle Phi-3 generation - FIXED: Now returns string directly
#             user_type = kwargs.get('user_type', 'student')
#             academic_level = kwargs.get('student_level', 'undergraduate')
#             content_type = kwargs.get('content_type', 'simplified_explanation')
            
#             result = self.phi3_generator.generate(prompt, user_type, academic_level, content_type)
#             return result
#         else:
#             # Use Groq for comparison - check if this is a large content request
#             is_large_content = len(prompt) > 8000  # You can adjust this threshold
            
#             if is_large_content:
#                 return self.groq_generator.generate_large_content(prompt)
#             else:
#                 return self.groq_generator.generate(prompt)
    
#     def get_service_status(self) -> dict:
#         """Get clean research-focused status"""
#         groq_status = self.groq_generator.get_service_status()
#         phi3_health = self.phi3_generator.health_check()
        
#         # Clean Groq status - remove model names, focus on providers
#         clean_groq_status = {
#             'healthy_providers': groq_status['healthy_providers'],
#             'total_providers': groq_status['total_providers'],
#             'providers': [
#                 {
#                     'name': provider['name'],
#                     'failures': provider['failures']
#                 }
#                 for provider in groq_status['providers']
#             ]
#         }
        
#         # Enhanced Phi-3 status
#         enhanced_phi3_status = {
#             'server_healthy': phi3_health['server_healthy'],
#             'model_available': phi3_health['model_available'],
#             'available_models': phi3_health['available_models'],
#             'model_required': phi3_health['model_required']
#         }
        
#         return {
#             "groq": clean_groq_status,
#             "phi3": enhanced_phi3_status
#         }


# # Global model manager instance
# model_manager = ModelManager()


# # Setup function for your Streamlit app
# def setup_generators():
#     """Setup both generators with health checks"""
#     print("🔧 Setting up generators...")
    
#     groq_generator = MultiGroqGenerator()
    
#     phi3_generator = HFGenerator()
#     phi3_health = phi3_generator.health_check()
    
#     print(f"🏥 Phi-3 Health: {phi3_health}")
    
#     if not phi3_health["server_healthy"]:
#         print("❌ Phi-3 server is not accessible")
#     elif not phi3_health["model_available"]:
#         print("🔄 Phi-3 model needs to be pulled on first use")
    
#     return {
#         "groq": groq_generator,
#         "phi3": phi3_generator
#     }


# # Test function
# def test_generators():
#     """Test both generators"""
#     print("🧪 Testing Generators...")
    
#     generators = setup_generators()
    
#     # Test Groq
#     print("\n🔷 Testing Groq...")
#     groq_result = generators["groq"].generate("Explain photosynthesis briefly")
#     if not groq_result.startswith("["):
#         print("✅ Groq working")
#     else:
#         print("❌ Groq failed:", groq_result)
    
#     # Test Phi-3
#     print("\n🔶 Testing Phi-3...")
#     phi3_result = generators["phi3"].generate("Explain photosynthesis briefly")
#     if "❌ Phi-3 Error:" not in phi3_result:
#         print("✅ Phi-3 working")
#     else:
#         print("❌ Phi-3 failed:", phi3_result)
    
#     # Test health
#     print("\n🏥 Health Check:")
#     print(f"Groq providers: {len(generators['groq'].providers)}")
#     print(f"Phi-3 healthy: {generators['phi3'].health_check()}")


# if __name__ == "__main__":
#     test_generators()
