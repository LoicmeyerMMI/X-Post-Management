import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import database
import bot

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)


def _process_due_posts():
    """Process posts that need action: schedule on X or post immediately."""

    # 1. Handle posts that need to be scheduled on X natively
    pending = database.get_pending_scheduled()
    for post in pending:
        post_id = post['id']
        scheduled_at = post.get('scheduled_at')
        if not scheduled_at:
            continue

        logger.info(f"Scheduling post #{post_id} on X for {scheduled_at}")
        database.update_post_status(post_id, 'scheduling')

        result = bot.post_to_x(
            text=post.get('text', ''),
            image_path=post.get('image_path', ''),
            scheduled_at=scheduled_at
        )

        if result.get('success'):
            database.update_post_status(post_id, 'scheduled_on_x')
            logger.info(f"Post #{post_id} scheduled on X successfully")
        else:
            error_msg = result.get('error', 'Unknown error')
            retries = post.get('retries_count', 0)
            max_retries = int(os.getenv('MAX_RETRIES', '1'))

            if retries < max_retries:
                database.update_post(
                    post_id,
                    status='scheduled',
                    error_message=error_msg,
                    retries_count=retries + 1
                )
                logger.warning(f"Post #{post_id} scheduling failed, will retry ({retries + 1}/{max_retries}): {error_msg}")
            else:
                database.update_post_status(post_id, 'error', error_message=error_msg)
                logger.error(f"Post #{post_id} scheduling failed permanently: {error_msg}")


def start():
    interval = int(os.getenv('CHECK_INTERVAL_SECONDS', '15'))
    scheduler.add_job(_process_due_posts, 'interval', seconds=interval, id='check_posts',
                      replace_existing=True, max_instances=1)
    scheduler.start()
    logger.info(f"Scheduler started (checking every {interval}s)")


def stop():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
