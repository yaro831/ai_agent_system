
# core/utils.py
"""
פונקציות עזר למערכת
"""
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional, List, Callable
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """מקודד JSON מותאם אישית לטיפול בסוגי נתונים מיוחדים"""
    
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif hasattr(obj, 'value'):
            return obj.value
        return super().default(obj)

def generate_task_id() -> str:
    """יצירת מזהה ייחודי למשימה"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8]
    return f"task_{timestamp}_{random_part}"

def generate_message_id() -> str:
    """יצירת מזהה ייחודי להודעה"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8]
    return f"msg_{timestamp}_{random_part}"

def safe_json_dumps(data: Any, **kwargs) -> str:
    """המרה בטוחה לJSON"""
    default_kwargs = {
        'ensure_ascii': False,
        'indent': 2,
        'cls': JSONEncoder
    }
    default_kwargs.update(kwargs)
    
    try:
        return json.dumps(data, **default_kwargs)
    except Exception as e:
        logger.error(f"Failed to serialize to JSON: {e}")
        return "{}"

def safe_json_loads(data: str) -> Dict[str, Any]:
    """המרה בטוחה מJSON"""
    try:
        return json.loads(data)
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {}

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """דקורטור לניסיון חוזר עם השהייה מתגברת"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise
                    
                    delay = min(base_delay * (exponential_base ** (retries - 1)), max_delay)
                    logger.warning(f"Retry {retries}/{max_retries} after {delay}s: {e}")
                    await asyncio.sleep(delay)
            
            return None
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise
                    
                    delay = min(base_delay * (exponential_base ** (retries - 1)), max_delay)
                    logger.warning(f"Retry {retries}/{max_retries} after {delay}s: {e}")
                    time.sleep(delay)
            
            return None
        
        return wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def sanitize_text(text: str) -> str:
    """ניקוי טקסט ממרכיבים מזיקים"""
    if not isinstance(text, str):
        return ""
    
    # הסרת תגי HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # הסרת תווים מיוחדים
    text = re.sub(r'[^\w\s\u0590-\u05FF.,!?-]', '', text)
    
    # הסרת רווחים כפולים
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_hebrew_text(text: str) -> str:
    """חילוץ טקסט עברי בלבד"""
    # שמירה על טקסט עברי, רווחים ופיסוק
    hebrew_text = re.sub(r'[^\u0590-\u05FF\s.,!?-]', '', text)
    return hebrew_text.strip()

def validate_email(email: str) -> bool:
    """אימות תקינות כתובת דוא"ל"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
    return bool(re.match(pattern, email))

def hash_sensitive_data(data: str) -> str:
    """הצפנת נתונים רגישים"""
    if not isinstance(data, str):
        data = str(data)
    
    salt = "ai_agent_system_salt"  # בפרודקשן - נטען מקובץ הגדרות
    return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()

class TimeoutError(Exception):
    """שגיאת פסק זמן"""
    pass

def with_timeout(seconds: int):
    """דקורטור לפסק זמן על פונקציה"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function '{func.__name__}' timed out after {seconds} seconds")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except TimeoutError:
                    raise TimeoutError(f"Function '{func.__name__}' timed out after {seconds} seconds")
        
        return wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """עיצוב תאריך ושעה"""
    return dt.strftime(format_string)

def parse_datetime(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """קריאת תאריך ושעה מטקסט"""
    return datetime.strptime(date_string, format_string)

def calculate_time_difference(start: datetime, end: datetime) -> Dict[str, int]:
    """חישוב הפרש זמן"""
    diff = end - start
    
    days = diff.days
    seconds = diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    
    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": remaining_seconds,
        "total_seconds": int(diff.total_seconds())
    }

class RateLimiter:
    """מגביל קצב לקריאות API"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """בדיקה האם ניתן לבצע קריאה"""
        now = time.time()
        
        # ניקוי קריאות ישנות
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """חישוב זמן ההמתנה הנדרש"""
        if not self.calls:
            return 0.0
        
        now = time.time()
        oldest_call = self.calls[0]
        return max(0, oldest_call + self.time_window - now)

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """חלוקת רשימה לחתיכות"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """מיזוג מילונים מעמיק"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """שטוח מילון מקונן"""
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)

class CircuitBreaker:
    """מעגל מניעה לטיפול בכשלים חוזרים"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def record_failure(self):
        """רישום כשל"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"
    
    def record_success(self):
        """רישום הצלחה"""
        self.failures = 0
        self.state = "closed"
    
    def is_open(self) -> bool:
        """בדיקה האם המעגל פתוח"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return False
            return True
        
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """ביצוע פונקציה תוך שמירה על המעגל"""
        if self.is_open():
            raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

class CircuitBreakerOpenError(Exception):
    """שגיאת מעגל פתוח"""
    pass

# פונקציות לניתוח ועיבוד טקסט
def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """חילוץ מילות מפתח מטקסט"""
    # הסרת stop words
    stop_words = {"אני", "את", "אתה", "אנחנו", "אתם", "אתן", "הוא", "היא", "הם", "הן",
                  "זה", "זו", "זאת", "אלה", "אילו", "על", "אל", "מעל", "מתחת", "מול",
                  "הנה", "הנני", "הרי", "מה", "מי", "איפה", "איה", "אי", "אין", "אינם",
                  "כאשר", "כי", "לכן", "בגלל", "למרות", "עם", "עימו", "עימה", "עימנו", "עימם"}
    
    # חילוץ מילים
    words = re.findall(r'\b\w+\b', text.lower())
    
    # סינון וספירה
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # מיון לפי תדירות
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in sorted_words[:max_keywords]]

def summarize_text(text: str, max_sentences: int = 3) -> str:
    """יצירת תקציר טקסט"""
    # פיצול לפסקאות ומשפטים
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return ""
    
    # יצירת תקציר (בסיסי)
    summary_sentences = sentences[:max_sentences]
    return " ".join(summary_sentences) + "."

def detect_language(text: str) -> str:
    """זיהוי שפת הטקסט"""
    # זיהוי בסיסי - הערביים והעברים
    hebrew_chars = set(range(0x0590, 0x05FF))
    english_chars = set(range(0x0041, 0x007A))
    
    hebrew_count = sum(1 for char in text if ord(char) in hebrew_chars)
    english_count = sum(1 for char in text if ord(char.lower()) in english_chars)
    
    if hebrew_count > english_count:
        return "he"
    elif english_count > hebrew_count:
        return "en"
    else:
        return "mixed"

# פונקציות למחזור מטמון
class Cache:
    """מטמון פשוט לשיפור ביצועים"""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, tuple] = {}  # (value, expiry_time)
        self.ttl = ttl
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """קבלת ערך מהמטמון"""
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expiry_time = self.cache[key]
            
            if time.time() > expiry_time:
                del self.cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """הוספת ערך למטמון"""
        with self.lock:
            expiry_time = time.time() + (ttl or self.ttl)
            self.cache[key] = (value, expiry_time)
    
    def delete(self, key: str) -> None:
        """מחיקת ערך מהמטמון"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self) -> None:
        """ניקוי המטמון"""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """מספר פריטים במטמון"""
        with self.lock:
            return len(self.cache)

# פונקציות לביצועי HTTP
def create_http_client(timeout: int = 30, retries: int = 3) -> Any:
    """יצירת לקוח HTTP עם קונפיגורציה בסיסית"""
    import httpx
    
    return httpx.Client(
        timeout=timeout,
        transport=httpx.HTTPTransport(retries=retries),
        follow_redirects=True
    )

def parse_url(url: str) -> Dict[str, str]:
    """פיענוח URL לרכיביו"""
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parsed.query,
        "fragment": parsed.fragment
    }

def build_url(base: str, path: str = "", params: Dict[str, str] = None) -> str:
    """בניית URL מרכיבים"""
    from urllib.parse import urljoin, urlencode
    
    url = urljoin(base, path)
    
    if params:
        query_string = urlencode(params)
        url = f"{url}?{query_string}"
    
    return url

# פונקציות לטיפול בקבצים
def ensure_directory(path: str) -> None:
    """ווידוא קיום תיקייה"""
    import os
    
    os.makedirs(path, exist_ok=True)

def read_file_safely(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """קריאת קובץ בטוחה"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None

def write_file_safely(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """כתיבת קובץ בטוחה"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return False

def get_file_size(file_path: str) -> int:
    """קבלת גודל קובץ"""
    import os
    
    try:
        return os.path.getsize(file_path)
    except:
        return 0

# פונקציות לניהול זיכרון
class MemoryMonitor:
    """מוניטור שימוש בזיכרון"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """קבלת שימוש נוכחי בזיכרון"""
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": process.memory_percent()
        }
    
    @staticmethod
    def log_memory_usage():
        """רישום שימוש בזיכרון"""
        usage = MemoryMonitor.get_memory_usage()
        logger.info(f"Memory usage: RSS={usage['rss']:.2f}MB, VMS={usage['vms']:.2f}MB, %={usage['percent']:.1f}%")

# פונקציות להמרת נתונים
def serialize_dataclass(obj: Any) -> Dict[str, Any]:
    """המרת dataclass למילון"""
    import dataclasses
    
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return obj.__dict__

def deserialize_dataclass(cls, data: Dict[str, Any]) -> Any:
    """המרת מילון ל-dataclass"""
    import dataclasses
    
    if dataclasses.is_dataclass(cls):
        return cls(**data)
    raise ValueError(f"{cls} is not a dataclass")

# פונקציות לחישובי סטטיסטיקה בסיסיים
def calculate_mean(numbers: List[float]) -> float:
    """חישוב ממוצע"""
    return sum(numbers) / len(numbers) if numbers else 0.0

def calculate_median(numbers: List[float]) -> float:
    """חישוב חציון"""
    if not numbers:
        return 0.0
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 0:
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        return sorted_numbers[n//2]

def calculate_std_dev(numbers: List[float]) -> float:
    """חישוב סטיית תקן"""
    if not numbers:
        return 0.0
    
    mean = calculate_mean(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    return variance ** 0.5

# פונקציות לטיפול בשגיאות
class ApplicationError(Exception):
    """שגיאה כללית באפליקציה"""
    
    def __init__(self, message: str, code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

class ValidationError(ApplicationError):
    """שגיאת אימות"""
    pass

class ConfigurationError(ApplicationError):
    """שגיאת קונפיגורציה"""
    pass

def handle_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """טיפול כללי בשגיאות"""
    error_info = {
        "type": type(error).__name__,
        "message": str(error),
        "context": context or {}
    }
    
    if isinstance(error, ApplicationError):
        error_info["code"] = error.code
        error_info["details"] = error.details
    
    logger.error(f"Error handled: {error_info}")
    return error_info

# פונקציות לגוגינג מערכתי
class SystemStatus:
    """סטטוס המערכת"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """קבלת מידע על המערכת"""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            "disk_usage": psutil.disk_usage('/').percent
        }
    
    @staticmethod
    def check_health() -> Dict[str, Any]:
        """בדיקת "בריאות" המערכת"""
        import psutil
        
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_usage_percent = psutil.disk_usage('/').percent
        
        health_status = {
            "status": "healthy",
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent,
            "disk_usage": disk_usage_percent,
            "timestamp": datetime.now().isoformat()
        }
        
        # קביעת סטטוס לפי ספים
        if cpu_percent > 90 or memory_percent > 90 or disk_usage_percent > 90:
            health_status["status"] = "critical"
        elif cpu_percent > 70 or memory_percent > 70 or disk_usage_percent > 80:
            health_status["status"] = "warning"
        
        return health_status

# פונקציות לתזמון משימות
class TaskScheduler:
    """תזמון משימות"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.thread = None
    
    def add_task(self, name: str, func: Callable, interval: float, *args, **kwargs):
        """הוספת משימה לתזמון"""
        self.tasks[name] = {
            "func": func,
            "interval": interval,
            "args": args,
            "kwargs": kwargs,
            "last_run": None,
            "next_run": time.time() + interval
        }
    
    def remove_task(self, name: str):
        """הסרת משימה"""
        if name in self.tasks:
            del self.tasks[name]
    
    def start(self):
        """התחלת התזמון"""
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """עצירת התזמון"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run_scheduler(self):
        """לולאת תזמון"""
        while self.running:
            current_time = time.time()
            
            for name, task in self.tasks.items():
                if current_time >= task["next_run"]:
                    try:
                        task["func"](*task["args"], **task["kwargs"])
                        task["last_run"] = current_time
                        task["next_run"] = current_time + task["interval"]
                    except Exception as e:
                        logger.error(f"Task '{name}' failed: {e}")
            
            time.sleep(1)

# פונקציות לניהול קונקשנים
class ConnectionPool:
    """מאגר קונקשנים"""
    
    def __init__(self, create_connection: Callable, max_size: int = 10):
        self.create_connection = create_connection
        self.max_size = max_size
        self.pool = asyncio.Queue(maxsize=max_size)
        self._initialized = False
    
    async def initialize(self):
        """אתחול המאגר"""
        if self._initialized:
            return
            
        for _ in range(self.max_size):
            connection = await self.create_connection()
            await self.pool.put(connection)
        
        self._initialized = True
    
    async def get_connection(self):
        """קבלת קונקשן מהמאגר"""
        if not self._initialized:
            await self.initialize()
        
        try:
            connection = await asyncio.wait_for(self.pool.get(), timeout=5.0)
            return connection
        except asyncio.TimeoutError:
            raise TimeoutError("No connection available in pool")
    
    async def release_connection(self, connection):
        """החזרת קונקשן למאגר"""
        if self.pool.full():
            try:
                connection.close()
            except:
                pass
        else:
            await self.pool.put(connection)
    
    async def close_all(self):
        """סגירת כל הקונקשנים"""
        while not self.pool.empty():
            connection = await self.pool.get()
            try:
                connection.close()
            except:
                pass
"""