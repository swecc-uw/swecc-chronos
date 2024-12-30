from app.services.dynamodb_service import db
import logging

try:
    db.create_health_metric_table()
except Exception as e:
    logging.error(f"Failed to create table: {e}")