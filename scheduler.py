from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils import fetch_rates
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_rates, CronTrigger(minute=1))  # every hour at :01
    scheduler.start()
    logger.info("Scheduler started.")