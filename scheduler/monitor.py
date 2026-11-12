from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from scheduler.jobs import job_price_monitoring, job_scheduled_ai_analysis
from utils.logger import logger


class PriceSchedulerMonitor:
    def __init__(self):
        self.scheduler = BlockingScheduler()

    def setup_jobs(self) -> None:
        interval_sec = settings.PRICE_MONITOR_INTERVAL
        logger.info(f"Adding price monitoring job every {interval_sec} seconds...")
        self.scheduler.add_job(
            job_price_monitoring,
            trigger=IntervalTrigger(seconds=interval_sec),
            id="price_monitoring_job",
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )

        ai_interval_min = settings.AI_ANALYSIS_INTERVAL_MINUTES
        logger.info(f"Adding scheduled AI analysis job every {ai_interval_min} minutes...")
        self.scheduler.add_job(
            job_scheduled_ai_analysis,
            trigger=IntervalTrigger(minutes=ai_interval_min),
            id="ai_analysis_job",
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )

    def start(self) -> None:
        self.setup_jobs()
        logger.info("Starting Price Scheduler Monitor...")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Price Scheduler Monitor stopped.")

