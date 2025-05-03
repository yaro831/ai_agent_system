"""
מודול הפעלה ראשי למערכת סוכני בינה מלאכותית
"""
import os
import sys
import logging
import argparse
import uvicorn
from dotenv import load_dotenv

# הוספת הספריה הנוכחית ל-path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# טעינת משתני סביבה
load_dotenv()

from ai_agent_system.config import settings
from ai_agent_system.core.agent_manager import AgentManager
from ai_agent_system.api.routes import create_app
from ai_agent_system.storage.database import Database

# הגדרת לוגינג
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'app.log'))
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """ניתוח ארגומנטים מהמשתמש"""
    parser = argparse.ArgumentParser(description='מערכת סוכני בינה מלאכותית')
    
    parser.add_argument('--host', type=str, default=settings.API_HOST,
                        help='Host לשרת ה-API')
    
    parser.add_argument('--port', type=int, default=settings.API_PORT,
                        help='Port לשרת ה-API')
    
    parser.add_argument('--debug', action='store_true', default=settings.DEBUG,
                        help='הפעלה במצב דיבאג')
    
    parser.add_argument('--no-api', action='store_true',
                        help='הפעלה ללא שרת API')
    
    parser.add_argument('--task', type=str,
                        help='ביצוע משימה בודדת והפסקה')
    
    return parser.parse_args()

def run_single_task(task_description: str):
    """
    ביצוע משימה בודדת
    
    Args:
        task_description: תיאור המשימה
    """
    logger.info(f"Running single task: {task_description}")
    
    # אתחול מנהל הסוכנים
    agent_manager = AgentManager()
    
    # ביצוע המשימה
    result = agent_manager.execute_task(task_description)
    
    # הדפסת התוצאה
    logger.info("Task completed")
    print("\n--- Task Result ---")
    print(f"Task ID: {result['task_id']}")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'completed':
        print("\nResult:")
        print(result['result'])
    else:
        print("\nError:")
        print(result.get('error', 'Unknown error'))

def main():
    """פונקציה ראשית"""
    # ניתוח ארגומנטים
    args = parse_arguments()
    
    # הגדרות מהארגומנטים
    host = args.host
    port = args.port
    debug = args.debug
    
    # יצירת תיקיית לוגים אם לא קיימת
    os.makedirs('logs', exist_ok=True)
    
    # הגדרת רמת לוגינג לפי מצב דיבאג
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting AI Agent System")
    
    # אם יש משימה בודדת - ביצוע והפסקה
    if args.task:
        run_single_task(args.task)
        return
    
    # אתחול מסד נתונים
    db = Database()
    logger.info("Database initialized")
    
    # אתחול מנהל הסוכנים
    agent_manager = AgentManager()
    logger.info("Agent Manager initialized")
    
    # אם לא ביקשו להפעיל ללא API
    if not args.no_api:
        logger.info(f"Starting API server on {host}:{port}")
        
        # יצירת אפליקציית FastAPI
        app = create_app()
        
        # הפעלת שרת
        uvicorn.run(app, host=host, port=port, log_level="info")
    else:
        logger.info("Running without API server")
        
        # לוגיקה להפעלה ללא API (למשל, הפעלה מבוססת קונסול)
        try:
            print("AI Agent System is running (Press Ctrl+C to exit)")
            # לולאה אינסופית שתחכה לסיום
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")

if __name__ == "__main__":
    main()